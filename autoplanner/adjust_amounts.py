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

class AmountAdjuster():
	"""
	Takes a single day's requirements, current requirements and at least one meal, and adjusts amounts to fit req
	Parameters:
		* adjust_mult: the minimum amount that can be used. Cannot be more than one. .25 or .5 common
	"""

	def __init__(self, req_cols, meal_incl_list, adjust_mult, user_id, plan_date, solver_rel_path, connection):
		"""
		Parameters
			* req_cols: nutrient abreviations for ub/lb columns to include
			* meal_incl_list: meals to be included in meal type
			* adjust_mult: minimum granularity
			* user_id: user id
		"""
		self.req_cols = req_cols
		self.meal_incl_list = meal_incl_list
		self.adjust_mult = adjust_mult
		self.user_id = user_id
		self.plan_date = plan_date
		self.solver_rel_path = solver_rel_path
		self.max_amt = 4
		self.connection = connection

	def solve_and_return_adjust(self):
		req_cols = self.req_cols
		meal_incl_list = self.meal_incl_list
		adjust_mult = self.adjust_mult
		user_id = self.user_id
		plan_date = self.plan_date
		solver_rel_path = self.solver_rel_path
		max_amt = self.max_amt
		connection = self.connection
		food_df_adj, reqs_df_adj = self.build_food_df(req_cols, meal_incl_list, user_id, plan_date, adjust_mult, connection)
		print(reqs_df_adj)
		model =self.build_adjust_model(food_df_adj, reqs_df_adj,req_cols,round(max_amt/adjust_mult))
		model = self.solve_model(model, solver_rel_path)
		return_df = self.parse_adj_model_results(model, food_df_adj, req_cols)
		return return_df

	def parse_adj_model_results(self, model, food_df, req_cols):
		sol_li =  [model.amt[i].value for i in range(0,len(food_df))]
		sol_li = [0 if s is None  else s for s in sol_li]
		return_df = food_df.assign(amt = sol_li)
		for req in req_cols: 
			return_df[req] = np.round(return_df[req]*return_df['amt'], 2)
		return return_df

	def build_food_df(self, req_cols, meal_incl_list, user_id, plan_date, adjust_mult, connection):
		"""
		Builds the dataset to be used by the simple adjust solve
		"""
		reqs_df = pd.read_sql(sql=self.query_reqs_adjust(), params={'user_id':user_id},con=connection)
		reqs_df = reqs_df.fillna(0)
		# Get all foods in meals for that day
		food_df = pd.read_sql(sql=self.query_food_adjust(), params={'user_id':user_id,'plan_date':plan_date}, con=connection)
		food_df['last_view'] = food_df['last_view'].fillna(datetime.date(2018,1,1))
		food_df['last_view'] = pd.to_datetime(food_df['last_view'])
		food_df['last_use'] = food_df['last_use'].fillna(datetime.date(2018,1,1))
		food_df['last_use'] = pd.to_datetime(food_df['last_use'])
		food_df = food_df.fillna(0)
		# Seperate included meals (adjust) from excluded (don't adjust)
		excl_df = food_df[~food_df['meal_type'].isin(meal_incl_list)]
		food_df_adj = food_df[food_df['meal_type'].isin(meal_incl_list)]
		food_df_adj.reset_index(inplace=True, drop=True)
		for req in req_cols:
			# This is where amount_divisor is crucial. It should just be the base amount of the serving size unit
			excl_df[req] = excl_df[req]*excl_df['amt']/excl_df['amount_divisor']

		# Add up nutrients 
		excl_df_sum = excl_df[req_cols].sum()
		excl_df_sum = pd.DataFrame(dict(zip(list( excl_df_sum.index), list(excl_df_sum.to_frame()[0]))), index=range(1))
		# Adjust the requirements df to subtract the nutrients from the foods not to be adjusted
		reqs_df_adj = reqs_df
		excl_df_stacked = excl_df_sum.append(excl_df_sum, ignore_index=True)
		excl_df_stacked.reset_index(inplace=True)
		if len(excl_df) >0:
			reqs_df_adj[req_cols] -= excl_df_stacked[req_cols]
			#reqs_df_adj.loc[0, req_cols] = reqs_df_adj.loc[0, req_cols] - excl_df_sum.loc[0, req_cols]
			#reqs_df_adj.loc[1, req_cols] = reqs_df_adj.loc[1, req_cols] - excl_df_sum.loc[0, req_cols]
		print(reqs_df_adj)
		# Set upper and lower bounds for foods to be adjusted. 
		max_amt = 4 # setting for now
		ub = max_amt/adjust_mult 
		# Set upper and lower bounds for each food. Done element-wise to be adjustable later
		food_df_adj= food_df_adj.assign(lb_col=1)
		food_df_adj= food_df_adj.assign(ub_col=np.round(food_df_adj['max_servings']/adjust_mult))
		# Multiply each nutrient by the adjustment factor. This normalizes each to start at '1' * adjust_mult. Allows an integer decision variable going forward
		for req in req_cols:
			food_df_adj[req] = np.round(food_df_adj[req].astype('float')*adjust_mult,2).astype('float')
		#prob_r = ((food_df_adj['removed']+0.001)/(food_df_adj['viewed']+0.002))*0.5  + food_df_adj['dislike_ind']*2 + np.random.rand(len(food_df_adj))*0.1 +1/(np.maximum([0.5]*len(food_df_adj), food_df_adj['viewed']-food_df_adj['removed']))*0.3  + (1/(((datetime.date.today()-food_df_adj['last_view'].dt.date).dt.days)+0.5))*0.2
		prob_r = (1-(food_df_adj['user_total_uses']+0.001)/(food_df_adj['viewed']+0.002))*0.3 \
				 + (5 -food_df_adj['user_star_rating'])*0.3 \
				 + np.random.rand(len(food_df_adj))*0.05 \
				 + 1/(np.maximum([0.5]*len(food_df_adj), food_df_adj['user_total_uses']))*0.3 \
				 + (1/(((datetime.date.today()-food_df_adj['last_view'].dt.date).dt.days)+0.5))*0.1 \
				 + (1/(((datetime.date.today()-food_df_adj['last_use'].dt.date).dt.days)+0.5))*0.25
		food_df_adj = food_df_adj.assign(prob_r = prob_r)
		return food_df_adj, reqs_df_adj

	def save_orig(self):
		"""
		Save original amounts for do / undo. But may not be necessary if implemented in Redux
		"""
		pass

	def solve_model(self, model, solver_rel_path):
		# goal_dir = os.path.join(os.getcwd(), solver_rel_path)
		# solverpath_exe = os.path.normpath(goal_dir)
		opt = SolverFactory('cbc',executable=solver_rel_path)
		opt.solve(model)
		return model 

	def build_adjust_model(self, food_df, reqs_df, req_cols, fd_mx):
		"""
		Builds adjust amounts model
		"""
		model=ConcreteModel()
		model.N = Set(initialize=req_cols) 
		food_df_dict = food_df[['prob_r']+req_cols].to_dict('list')
		model.bounds = Param(model.N, initialize=reqs_df[req_cols].to_dict('list'))
		model.full_I = Set(initialize=food_df.index)
		model.amt = Var(model.full_I,bounds=(1,fd_mx),within=NonNegativeIntegers) 
		model.amt_lb = Param(model.full_I, initialize=food_df[['lb_col']].to_dict('dict')['lb_col']) # 2x len(full_i)
		model.amt_ub = Param(model.full_I, initialize=food_df[['ub_col']].to_dict('dict')['ub_col']) # 2x len(full_i)

		def ml_bounds(model,n):
		    return (model.bounds[n][0], summation(food_df_dict[n],model.amt), model.bounds[n][1])

		model.nutr_constr = Constraint(model.N, rule=ml_bounds)
		
		def amt_bounds(model, i):
			return (model.amt_lb[i] , model.amt[i] , model.amt_ub[i]) 

		model.amt_constr = Constraint(model.full_I, rule=amt_bounds)

		# Meal Minimums	
		# def br_min(model):
		# 	return (ml_min_list[0], summation(food_df_dict['calories'],model.amt),reqs_df['calories'][1]-ml_min_list[1]-ml_min_list[2])
		# model.br_min_const = Constraint(expr=br_min(model))

		# def lu_min(model):
		# 	return  (ml_min_list[1], summation(food_df_dict['calories'],model.amt), reqs_df['calories'][1]-ml_min_list[0]-ml_min_list[2])
		# model.lu_min_const = Constraint(expr=lu_min(model))

		# def di_min(model):
		# 	return (ml_min_list[2], summation(food_df_dict['calories'],model.amt), reqs_df['calories'][1]-ml_min_list[0]-ml_min_list[1])
		# model.di_min_const = Constraint(expr=di_min(model))
		# def cal_min(model):
		#     return  summation(food_df_dict['calories'],model.amt) >= reqs_df['calories'][0]

		# model.cal_bounds = Constraint(expr=cal_min(model))
		def tgt_obj(model):
		    return  summation(food_df_dict['prob_r'],model.amt)
		
		model.obj = Objective(rule=tgt_obj)

		return model

	def query_reqs_adjust(self):
		return """
			SELECT 
				cal_lb as calories,
				pro_lb as protein_g,
				fat_lb as fat_g,
				car_lb as carb_g,
				fib_lb as fiber_g,
				clc_lb as calcium_mg,
				irn_lb as iron_mg,
				vta_lb as vit_a_mcg,
				vtc_lb as vit_a_mg,
				sug_lb as sugar_g,
				stf_lb as saturated_fat_g,
				sod_lb as sodium_mg,
				cho_lb as cholesterol_mg
			FROM core_profile
			WHERE user_id = %(user_id)s
			UNION
			SELECT
				cal_ub as calories,
				pro_ub as protein_g,
				fat_ub as fat_g,
				car_ub as carb_g,
				fib_ub as fiber_g,
				clc_ub as calcium_mg,
				irn_ub as iron_mg,
				vta_ub as vit_a_mcg,
				vtc_ub as vit_a_mg,
				sug_ub as sugar_g,
				stf_ub as saturated_fat_g,
				sod_ub as sodium_mg,
				cho_ub as cholesterol_mg
			FROM core_profile
			WHERE user_id = %(user_id)s
		"""

	def query_food_adjust(self):
		"""
		There is a get_day_plan method already in views.py, but the difference is that this allows a different post-query formatting ('list', rather than 'records' dict)
		Also will always need all meals for this case
		"""
		return """
		SELECT
		  am.meal_id,
		  am.amt,
		  am.amount_divisor,
		  am.serving_size_idx,
		  p.meal_type,
		  COALESCE(pr.default_dish_num, f.default_dish_num) as dish_num,
		  pr.viewed,
		  pr.user_total_uses,
		  COALESCE(pr.user_star_rating, f.star_rating) as user_star_rating,
		  pr.last_use,
		  pr.removed,
		  pr.dislike_ind,
		  pr.last_view,
		  COALESCE(pr.max_servings, f.max_servings) as max_servings,
		  f.food_key,
		  f.food_description,
		  f.brand,
		  f.serving_size_val,
		  f.food_type_grp,
		  f.calories, 
		  f.protein_g,
		  f.fat_g,
		  f.carb_g,
		  f.fiber_g,
		  f.calcium_mg,
		  f.iron_mg,
		  f.vit_a_mcg,
		  f.vit_c_mg,
		  f.sugar_g,
		  f.saturated_fat_g,
		  f.sodium_mg,
		  f.cholesterol_mg,
		  f.image_url,
		  ss.serving_sizes

		FROM plan_planmeal p
		JOIN plan_meal m
		   ON p.meal_id=m.id
		JOIN plan_food_amount am
		  ON m.id = am.meal_id
		JOIN food_foods f
		  ON f.food_key = am.food_id
		JOIN food_altservingsize ss
		  ON f.food_key = ss.food_id
		LEFT JOIN core_userprobrejectfood pr
		  ON f.food_key = pr.food_id
		  AND pr.user_id=%(user_id)s
		WHERE plan_date = %(plan_date)s and p.user_id=%(user_id)s;
		"""