# Takes about 15 seconds
from __future__ import division
import pandas as pd 
import numpy as np 
import datetime
import os
from pyomo.environ import *
from pyomo.opt import SolverFactory
from pyomo.gdp import *
import pyutilib.subprocess.GlobalData
pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False


class AlternativesEngine():

	def __init__(self, reqs_dict, food_df, food_key, user_id, plannum, meal_type, connection, solverpath_exe):
		"""
		reqs_dict: {'cal_lb':50, 'cal_ub':100, 'pro_lb':5, 'pro_ub':10...}
		"""
		self.reqs_dict = reqs_dict
		self.food_df = food_df
		self.food_key = food_key
		self.user_id = user_id
		self.plannum = plannum
		self.meal_type = meal_type
		self.connection = connection
		self.solverpath_exe = solverpath_exe

	def return_menu_df_oth_df_sim_df(self):
		reqs_dict = self.reqs_dict
		food_df = self.food_df
		food_key = self.food_key
		user_id = self.user_id
		plannum = self.plannum
		meal_type = self.meal_type
		connection = self.connection
		solverpath_exe = self.solverpath_exe
		alt_df = self.find_alternates(reqs_dict, food_df)
		alt_df = self.make_drag_key(alt_df, plannum, meal_type)
		sim_df = self.find_similar(food_key, alt_df, reqs_dict, food_df)
		sim_df = self.make_drag_key(sim_df, plannum, meal_type)
		return alt_df, sim_df

	def find_alternates(self, reqs_dict, food_df):
		plannum = self.plannum
		meal_type = self.meal_type
		alt_df = self.no_opt_solve(reqs_dict, food_df)
		alt_df = alt_df.assign(amt= alt_df['amt'] * alt_df['serving_size_val'])
		alt_df = alt_df.assign(serving_size_idx=0)
		alt_df = alt_df.assign(amount_divisor = alt_df['serving_size_val'])
		alt_df = self.make_drag_key(alt_df, plannum, meal_type)
		return alt_df

	def find_similar(self, food_key, alt_df, reqs_dict, food_df, connection):
		plannum = self.plannum
		meal_type = self.meal_type
		sim_food_df = food_df[~food_df['food_key'].isin(alt_df['food_key'])]
		req_cols = list(set([req[0:3] for req in reqs_dict.keys() if 'cal' not in req]))
		tgt_food_df = self.query_single_food(food_key, connection)
		sim_df = self.get_closest_greedy(req_cols, food_df, tgt_food_df)
		sim_df = sim_df.assign(amt=sim_df['serving_size_val'])
		sim_df = sim_df.assign(serving_size_idx=0)
		sim_df = sim_df.assign(amount_divisor=sim_df['serving_size_val'])
		alt_df = self.make_drag_key(alt_df, plannum, meal_type)
		return sim_df

	def make_drag_key(self, df, plannum, meal_type):
		drag_key_ser = df['food_key'].astype(str)+"_"+plannum+"_"+meal_type+"_alt"
		df = df.assign(drag_key = drag_key_ser)
		df = df.assign(drag_id = drag_key_ser)
		return df

	def process_model(self,model, food_df):
		sol_li =  [model.amt[i].value for i in range(0,len(food_df))]
		sol_li = [0 if s is None  else s for s in sol_li]
		food_df = food_df.assign(amt = sol_li)
		return_df = food_df[food_df['amt']>0]
		return return_df

	def solve_model(self, model, solverpath_exe):
		opt = SolverFactory('cbc',executable=solverpath_exe)
		opt.solve(model)
		return model

	def build_alt_model(self, reqs_dict, food_df, fd_mx):
		"""
		Build Alt Model
		"""
		abrev_to_nut_dict={'cal':'calories','pro':'protein_g','fat':'fat_g','car':'carb_g','fib':'fiber_g',
						'clc':'calcium_mg','irn':'iron_mg','vta':'vit_a_mcg','vtc':'vit_c_mg','sug':'sugar_g','stf':'saturated_fat_g','sod':'sodium_mg', 'cho':'cholesterol'}
		req_cols = list(set([abrev_to_nut_dict[req[0:3]] for req in reqs_dict.keys()]))
		reqs_df_dict ={}
		for req in reqs_dict.keys():
			nut_abrev = req[0:3]
			nutrient = abrev_to_nut_dict[nut_abrev]
			if nutrient not in reqs_df_dict:
				reqs_df_dict[nutrient] = [reqs_dict[nut_abrev+"_lb"], reqs_dict[nut_abrev+"_ub"]]
		#reqs_df = pd.DataFrame(reqs_df_dict)
		model = ConcreteModel()
		model.N = Set(initialize=req_cols)
		model.full_I = Set(initialize=food_df.index)
		food_df_dict = food_df[['prob_r']+req_cols].to_dict('list')
		model.bounds = Param(model.N, initialize=reqs_df_dict)
		model.food_ind = Var(model.full_I, within=Binary)
		model.m = fd_mx + 3
		model.amt = Var(model.full_I, bounds=(0,fd_mx),within=NonNegativeIntegers)
		def single_fd_big_m(request,i):
			return model.amt[i] <= model.food_ind[i] *model.m
		
		model.big_m_constr = Constraint(model.full_I, rule=single_fd_big_m)
		def single_fd(model):
			return summation(np.ones(len(food_df)).tolist(),model.food_ind) ==1
		
		model.single_fd_constr = Constraint(rule=single_fd)
		def ml_bounds(model,n):
			return (model.bounds[n][0], summation(food_df_dict[n],model.amt), model.bounds[n][1])
		
		model.nutr_bounds = Constraint(model.N, rule=ml_bounds)
		def tgt_obj(model):
			return  summation(food_df_dict['prob_r'],model.amt)
		
		model.obj = Objective(rule=tgt_obj) 
		# Be able to variably set the amount and the bounds 
		return model

	def compare_reqs_and_cols(self,reqs_dict,loop_df,j):
		abrev_to_nut_dict={'cal':'calories','pro':'protein_g','fat':'fat_g','car':'carb_g','fib':'fiber_g',
						'clc':'calcium_mg','irn':'iron_mg','vta':'vit_a_mcg','vtc':'vit_c_mg','sug':'sugar_g','stf':'saturated_fat_g','sod':'sodium_mg', 'cho':'cholesterol'}
		#req_cols = list(set([abrev_to_nut_dict[req[0:3]] for req in reqs_dict.keys()]))
		req_abrevs = list(set([req[0:3] for req in reqs_dict.keys()]))
		for nut_abrev in req_abrevs:
			nutrient = abrev_to_nut_dict[nut_abrev]
			loop_df =loop_df[(loop_df[nutrient]*j>=reqs_dict[nut_abrev+"_lb"])&(loop_df[nutrient]*j<=reqs_dict[nut_abrev+"_ub"])]
		loop_df = loop_df.assign(amt=j)
		return loop_df

	def no_opt_solve(self, reqs_dict,food_df):
		"""
		Solve model by multipying nutrients by 1,2 and 3 (or up to max servings for each) and checking if fits constraints
		"""
		final_df = self.compare_reqs_and_cols( reqs_dict, food_df, 1)
		if final_df.empty:
			final_df = pd.DataFrame()
		max_amt = max(food_df['max_servings'])
		for j in range(2,int(max_amt)+1):
		    loop_df = food_df[food_df['max_servings']<=j]
		    res_df = self.compare_reqs_and_cols(reqs_dict,loop_df,j)
		    res_df = res_df.assign(amt=j)
		    if len(loop_df) >0:
		        final_df = final_df.append(res_df)
		return final_df

	def get_closest_greedy(self, req_cols, food_df, tgt_food_df):
		"""
		Finds most similar foods that weren't included in alternatives from menu
		"""
		fd_idx_cols = [req+"_index" for req in req_cols]
		tgt_list = list(tgt_food_df[fd_idx_cols].values) # Target food index needs to be reset before adding 
		for i in food_df.index:
			oth_list = list(food_df.loc[i,fd_idx_cols].values)
			food_df.loc[i,'tgt_dist'] = np.sqrt(np.sum(np.square([(tgt_list[j]-oth_list[j]) for j in range(len(tgt_list))])))
		oth_foods_sorted = food_df.sort_values(by=['tgt_dist'],ascending=True)
		return oth_foods_sorted.iloc[0:3,]

	def query_single_food(self, food_key, connection):
		single_food_qry ="""
		SELECT
			f.food_key,
			fi.*
		FROM  food_foods f
		JOIN food_foodindex fi
			ON f.food_key = fi.food_id
		WHERE f.food_key = %(food_key)s
		"""
		tgt_food_df = pd.read_sql(sql=single_food_qry, params={'food_key':food_key}, con=connection)
		tgt_food_df = tgt_food_df.fillna(0)
		return tgt_food_df

	def query_alts_from_menu(self):
		pass

	def query_alts_from_oth(self):
		pass