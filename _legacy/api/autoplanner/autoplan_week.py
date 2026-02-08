# Takes about 15 seconds
from __future__ import division
import pandas as pd 
import numpy as np 
#import cloudpickle
import datetime
import os
from pyomo.environ import *
from pyomo.opt import SolverFactory
from pyomo.gdp import *
import pyutilib.subprocess.GlobalData
pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False

class WeekAutoPlanner():
	"""
	Takes client side variables to build a weekly plan and includes methods to:
		* build and query data
		* preprocess data into optimization parameters
		* build and solve optimization
		* return results or info about solve
	"""
	def __init__(self, connection, user_id, requirements_dict, menus_dict_list,week_start_dt, week_end_dt, n_snack, solver_rel_path, solver_params_dict):
		self.connection = connection
		self.user_id = user_id
		self.requirements_dict = requirements_dict
		self.menus_list = menus_dict_list
		self.week_start_dt = week_start_dt
		self.week_end_dt = week_end_dt
		self.n_snack = n_snack
		self.solver_rel_path = solver_rel_path
		self.solver_params_dict = solver_params_dict
		self.sides_dict ={'Breakfast':{'min':1,'max':2},'Lunch':{'min':1,'max':2},'Dinner':{'min':1,'max':2}}

	def solve_and_return_weekplan(self):
		"""
		Query, build and solve a model
		"""
		connection = self.connection
		user_id = self.user_id 
		requirements_dict = self.requirements_dict
		menus_list = self.menus_list
		week_start_dt = self.week_start_dt
		week_end_dt = self.week_end_dt
		n_snack = self.n_snack
		sides_dict = self.sides_dict
		qry = self.all_menu_opts_qry()
		solver_rel_path = self.solver_rel_path
		solver_params_dict = self.solver_params_dict
		# Query data and set relevant variables
		tag_id_tup, rest_id_tup, menu_id_tup, meals_idx_tup, days_list = self.prep_query_params(menus_list)
		params={'user_id': user_id, 'week_start_dt':week_start_dt, 'week_end_dt':week_end_dt, 'menu_id_list':menu_id_tup, 'tag_id_list':tag_id_tup, 'rest_id_list':rest_id_tup}
		food_df = self.query_food_df(connection, params, qry)
		# Create dataset
		opt_input_df, leftover_dict = self.build_opt_dataset(menus_list, food_df)
		opt_input_df.to_csv("opt_input_df.csv", index=False)
		# Set optimization variables
		food_max, global_m, meal_food_tup, src_constr_dict, incl_dict = self.set_opt_variables(opt_input_df, days_list, meals_idx_tup)
		# Build_autoplan_week_model
		model = self.build_autoplan_week_model(opt_input_df,requirements_dict,food_max,n_snack,global_m,
			src_constr_dict,incl_dict,sides_dict,meal_food_tup, meals_idx_tup, days_list, leftover_dict )
		# Solve weekplan
		model = self.solve_weekplan_model(solver_rel_path, model, solver_params_dict)
		# Parse results
		results_df = self.parse_weekplan_model_results(model, opt_input_df, leftover_dict)
		return results_df, model

	def resolve_weekplan(self, curr_plan_list, n_repl_dict):
		"""
		Query, build and solve a model
		"""
		connection = self.connection
		user_id = self.user_id 
		requirements_dict = self.requirements_dict
		menus_list = self.menus_list
		week_start_dt = self.week_start_dt
		week_end_dt = self.week_end_dt
		n_snack = self.n_snack
		sides_dict = self.sides_dict
		qry = self.all_menu_opts_qry()
		solver_rel_path = self.solver_rel_path
		solver_params_dict = self.solver_params_dict
		# Query data and set relevant variables
		tag_id_tup, rest_id_tup, menu_id_tup, meals_idx_tup, days_list = self.prep_query_params(menus_list)
		params={'user_id': user_id, 'week_start_dt':week_start_dt, 'week_end_dt':week_end_dt, 'menu_id_list':menu_id_tup, 'tag_id_list':tag_id_tup, 'rest_id_list':rest_id_tup}
		food_df = self.query_food_df(connection, params, qry)
		# Create dataset
		opt_input_df, leftover_dict = self.build_opt_dataset(menus_list, food_df)
		# Update max servings if already here 
		# Set optimization variables
		food_max, global_m, meal_food_tup, src_constr_dict, incl_dict = self.set_opt_variables(opt_input_df, days_list, meals_idx_tup)
		# Add current foods restrictions
		dishes = ['Whole Meals', 'Main Courses', 'Sides']
		access_idx_list = []
		get_day_reqs_list = []
		for meal_item in curr_plan_list:
			day = meal_item['day']
			meal = meal_item['meal']
			foods_list = meal_item['foods_list']
			for food in foods_list:
				amt  = round(food['amt']/food['serving_sizes']['ss_amts'][food['serving_size_idx']])
				updt_rows = ((opt_input_df['day']==day)&
							(opt_input_df['meal']==meal) &
							(opt_input_df['fd_type'] =='food') &
							(opt_input_df['unique_id']==food['food_key']))
				opt_input_df.loc[updt_rows, 'max_servings'] = max([0, amt-1]) # will return infeasible if less than 0
				# subtract additional foods
				# need to validate the algebra here
				if n_repl_dict[day] != 4:
					for key, val in requirements_dict[day].items():
						# Should check and only update if all four are not selected for a day. If that's the case, should just use full reqs.
						# qry - qry_user_reqs
						requirements_dict[day][key][0] += food[key]*amt
						requirements_dict[day][key][1] += food[key]*amt
				else:
					get_day_reqs_list.append(day)
		if len(get_day_reqs_list) >0:
			get_day_reqs_list = list(set(get_day_reqs_list))
			reqs_qry = self.user_reqs_qry()
			user_reqs = pd.read_sql(sql=reqs_qry, params={'user_id':user_id}, con=connection)
			user_reqs = user_reqs.fillna(0)
			user_reqs_dict = user_reqs.to_dict('list')
			for day in get_day_reqs_list:
				reqs_list = list(requirements_dict[day].keys())
				requirements_dict[day] = user_reqs[reqs_list].to_dict('list')

		# Build_autoplan_week_model
		model = self.build_autoplan_week_model(opt_input_df,requirements_dict,food_max,n_snack,global_m,
			src_constr_dict,incl_dict,sides_dict,meal_food_tup, meals_idx_tup, days_list, leftover_dict)
		# Solve weekplan
		model = self.solve_weekplan_model(solver_rel_path, model, solver_params_dict)
		# Parse results
		results_df = self.parse_weekplan_model_results(model, opt_input_df, leftover_dict)
		return results_df, model

	def solve_again_weekplan(self, saved_model, curr_plan_list):
		"""
		Resolve a weekplan
		"""
		solver_params_dict = self.solver_params_dict
		solver_rel_path = self.solver_rel_path
		menus_list = self.menus_list
		leftover_dict = self.build_just_leftover_dict(menus_list)
		model = self.exclude_prev_sol(saved_model) # do the fixed variables stay fixed? If not, need to use a constraint
		model = self.solve_weekplan_model(solver_rel_path, model, solver_params_dict)
		results_df = self.parse_results_by_access_idx(model, leftover_dict) # this is another good use of access_idx. Don't want to have to keep pulling opt_input_df
		return results_df, model

	def solve_and_return_all_weekplans(self):
		"""
		"""
		connection = self.connection
		user_id = self.user_id 
		requirements_dict = self.requirements_dict
		menus_list = self.menus_list
		week_start_dt = self.week_start_dt
		week_end_dt = self.week_end_dt
		n_snack = self.n_snack
		sides_dict = self.sides_dict
		qry = self.all_menu_opts_qry()
		solver_rel_path = self.solver_rel_path
		solver_params_dict = self.solver_params_dict
		#food_df, meals_idx_tup, days_list = self.query_datasets(connection,user_id,menus_list, week_start_dt, week_end_dt, qry)
		food_df = self.query_food_df(self, connection, user_id, params, qry)
		# Create dataset
		opt_input_df, leftover_dict = self.build_opt_dataset(menus_list, food_df)
		# Set optimization variables
		food_max, global_m, meal_food_tup, src_constr_dict, incl_dict = self.set_opt_variables(opt_input_df, days_list, meals_idx_tup)
		# Build_autoplan_week_model
		model = self.build_autoplan_week_model(opt_input_df,requirements_dict,food_max,n_snack,global_m,
			src_constr_dict,incl_dict,sides_dict,meal_food_tup, meals_idx_tup, days_list, leftover_dict)
		model = self.solve_weekplan_model(solver_rel_path, model,solver_params_dict)
		results_df = self.parse_weekplan_model_results(model, opt_input_df, leftover_dict)
		full_results_df = pd.DataFrame()
		i =1
		# Solve as many times as possible. 
		while not results_df.empty:
			results_df = results_df.assign(solve_num=i)
			full_results_df = full_results_df.append(results_df)
			model = self.exclude_prev_sol(model)
			model = self.solve_weekplan_model(solver_rel_path, model,solver_params_dict)
			results_df = self.parse_weekplan_model_results(model, opt_input_df, leftover_dict)
			i+=1
		return results_df, model

	def solve_weekplan_and_return_times(self):
		from timeit import default_timer as timer
		connection = self.connection
		user_id = self.user_id 
		requirements_dict = self.requirements_dict
		menus_list = self.menus_list
		week_start_dt = self.week_start_dt
		week_end_dt = self.week_end_dt
		n_snack = self.n_snack
		sides_dict = self.sides_dict
		qry = self.all_menu_opts_qry()
		solver_rel_path = self.solver_rel_path
		solver_params_dict = self.solver_params_dict
		# establish timing dict
		timing_dict = {}
		# Query data and set relevant variables
		start = timer()
		tag_id_tup, rest_id_tup, menu_id_tup, meals_idx_tup, days_list = self.prep_query_params(menus_list)
		end = timer()
		duration = end-start
		timing_dict['prep_query_params'] = [duration]
		# Query food df
		start = timer()
		params={'user_id': user_id, 'week_start_dt':week_start_dt, 'week_end_dt':week_end_dt, 'menu_id_list':menu_id_tup, 'tag_id_list':tag_id_tup, 'rest_id_list':rest_id_tup}
		food_df = self.query_food_df(connection, params, qry)
		end = timer()
		duration = end-start
		timing_dict['query_food_df'] = [duration]
		# Create dataset
		start = timer()
		opt_input_df, leftover_dict = self.build_opt_dataset(menus_list, food_df)
		end = timer()
		duration = end-start
		timing_dict['build_opt_dataset'] = [duration]
		# Set optimization variables
		start = timer()
		food_max, global_m, meal_food_tup, src_constr_dict, incl_dict = self.set_opt_variables(opt_input_df, days_list, meals_idx_tup)
		end = timer()
		duration = end-start
		timing_dict['set_opt_variables'] = [duration]
		# Build_autoplan_week_model
		start = timer()
		model = self.build_autoplan_week_model(opt_input_df,requirements_dict,food_max,n_snack,global_m,
			src_constr_dict,incl_dict,sides_dict,meal_food_tup, meals_idx_tup, days_list, leftover_dict)
		end = timer()
		duration = end-start
		timing_dict['build_autoplan_week_model'] = [duration]
		# Solving autoplan model
		start = timer()
		model = self.solve_weekplan_model(solver_rel_path, model, solver_params_dict)
		end = timer()
		duration = end-start
		timing_dict['solve_weekplan_model'] = [duration]
		# Parsing results
		start = timer()
		results_df = self.parse_weekplan_model_results(model, opt_input_df, leftover_dict)
		end = timer()
		duration = end-start
		timing_dict['parse_weekplan_model_results'] = [duration]
		return results_df, timing_dict, model

	def meal_alternatives_fresh_model(self, access_idx_list):
		connection = self.connection
		user_id = self.user_id 
		requirements_dict = self.requirements_dict
		menus_list = self.menus_list
		week_start_dt = self.week_start_dt
		week_end_dt = self.week_end_dt
		n_snack = self.n_snack
		sides_dict = self.sides_dict
		qry = self.all_menu_opts_qry()
		solver_rel_path = self.solver_rel_path
		solver_params_dict = self.solver_params_dict
		# Query data and set relevant variables
		tag_id_tup, rest_id_tup, menu_id_tup, meals_idx_tup, days_list = self.prep_query_params(menus_list)
		params={'user_id': user_id, 'week_start_dt':week_start_dt, 'week_end_dt':week_end_dt, 'menu_id_list':menu_id_tup, 'tag_id_list':tag_id_tup, 'rest_id_list':rest_id_tup}
		food_df = self.query_food_df(connection, params, qry)
		# Create dataset
		opt_input_df, leftover_dict = self.build_opt_dataset(menus_list, food_df)
		# Set optimization variables
		food_max, global_m, meal_food_tup, src_constr_dict, incl_dict = self.set_opt_variables(opt_input_df, days_list, meals_idx_tup)
		# Build_autoplan_week_model
		model = self.build_autoplan_week_model(opt_input_df,requirements_dict,food_max,n_snack,global_m,
			src_constr_dict,incl_dict,sides_dict,meal_food_tup, meals_idx_tup, days_list, leftover_dict)
		model = self.exclude_solutions_by_access_idx(model, access_idx_list)
		# Solve weekplan
		model = self.solve_weekplan_model(solver_rel_path, model, solver_params_dict)
		# Parse results
		results_df = self.parse_weekplan_model_results(model, opt_input_df, leftover_dict)
		return results_df

	def meal_alternatives_nth_solve(self):
		pass

	def full_plan_alternatives_nth_solve(self):
		pass

	def parse_results_by_access_idx(self, model, leftover_dict):
		"""
		need to return a df with the following (order not important):
			0 - index
			1 - unique_id
			2 - day
			3 - meal
			4 - dish_num
			5 - fd_type
			6 - amt
			7 - serving size val
		"""
		return_df = pd.DataFrame()
		for i in model.full_I:
			amt = model.amt[i].value
			if amt >0:
				access_idx_str = model.full_I_lkup[i]
				unique_id, fd_type, day, meal, dish_num, serving_size_val = access_idx_str.split('_')
				loop_dict = {
					'unique_id':[unique_id],
					'fd_type':[fd_type],
					'day':[day],
					'meal':[meal],
					'dish_num':[dish_num],
					'serving_size_val':[float(serving_size_val)],
					'amt':[amt]
				}
				loop_df = pd.DataFrame(loop_dict)
				return_df = return_df.append(loop_df)
		# Append leftover solves
		if not return_df.empty:
			for day in return_df['day'].unique():
				if day in leftover_dict: # checking if key e.g. 'day3' in leftover dict
					# Get the 
					meal_df = return_df[(return_df['meal']==leftover_dict[day]['orig_meal'])&\
		                           (return_df['day']==leftover_dict[day]['orig_day'])]
		            # Reassign the meal and day
					meal_df['day'] = day
					meal_df['meal'] = leftover_dict[day]['meal']
					return_df = return_df.append(meal_df)

		return return_df


	def parse_weekplan_model_results(self, model, opt_input_df, leftover_dict):
		"""
		Parses and returns a weekplan model
		""" 
		return_df = pd.DataFrame()
		amt_vec = [model.amt[i].value for i in model.full_I]
		amt_vec = [0 if s is None else s for s in amt_vec]
		fd_df=opt_input_df.assign(amt=amt_vec)  
		fd_df = fd_df[fd_df['amt']>0]
		fd_df = fd_df[['unique_id','day','meal','dish_num', 'fd_type', 'amt', 'serving_size_val']]
		for day in opt_input_df['day'].unique():
			if day in leftover_dict: # checking if key e.g. 'day3' in leftover dict
				# Get the 
				meal_df = fd_df[(fd_df['meal']==leftover_dict[day]['orig_meal'])&\
	                           (fd_df['day']==leftover_dict[day]['orig_day'])]
	            # Reassign the meal and day
				meal_df['day'] = day
				meal_df['meal'] = leftover_dict[day]['meal']
				fd_df = fd_df.append(meal_df)
		return fd_df

	def check_nut_constraints(self, solved_df, opt_input_df, requirements_dict):
		"""
		Checks that nutrient requirements were met on a day level
		Cumbersome because of the varying nutritional requirements by day element
		"""
		solved_df = solved_df.merge(opt_input_df, on=['unique_id','day','meal','dish_num', 'fd_type',  'serving_size_val'])
		days = list(solved_df['day'].unique())
		res_dict = {}
		for day in days:
			nutrient_df = pd.DataFrame(requirements_dict[day])
			nut_cols = list(nutrient_df.columns.values)
			solved_grp_df = solved_df[solved_df['day']==day][['day']+nut_cols].groupby('day').sum()
			res_dict[day] = True
			for nut in nut_cols:
				print(nut +" total "+str(solved_grp_df[nut][0]))
				print(nut + " upper bound: " +str(nutrient_df[nut][0]) +" "+ nut+" lower bound: "+str(nutrient_df[nut][1]) )
				if (nutrient_df[nut][1] > solved_grp_df[nut][0]) or (nutrient_df[nut][0] < solved_grp_df[nut][0]):
					res_dict[day] = False
					print("failed for "+nut+" for day "+day)
		print(res_dict)
		return res_dict

	def parse_solver_params(self,opt_object, params_dict):
		"""
		Add params to opt options
		"""
		for key, val in params_dict.items():
			opt_object.options[key] = val
		return opt_object

	def solve_weekplan_model(self,solver_rel_path, model, params_dict):
		"""
		Solves and returns model
		"""
		#instance = model.create_instance()
		goal_dir = os.path.join(os.getcwd(),solver_rel_path)
		solverpath_exe = os.path.normpath(goal_dir)
		opt = SolverFactory('cbc',executable=solverpath_exe) # Can change here with newest version
		opt = self.parse_solver_params(opt, params_dict)
		opt.solve(model)

		return model

	def save_model_to_s3(self, user_id, model):
		# Probably want to read and write to s3 from plan view
		pass

	def exclude_prev_sol(self, model):
		"""
		Excludes all foods / meals from previous solutions
		"""
		for i in model.full_I:
			if model.amt[i] != 0:
				model.amt[i].fix(0)
		return model

	def exclude_solutions_by_access_idx(self, model, access_idx_list):
		"""
		Modifies weekplan model. I.e. for alternatives
		unique_id_list: [
			{'access_idx': 'foo', 'amt': n}
		]
		"""
		for access_dict in access_idx_list:
			i = model.access_idx_lkup[access_dict['access_idx']]
			model = self.modify_autoplan_week_model(model, i, access_dict['amt'])
		return model

	def modify_autoplan_week_model(self, model, i, amt):
		if amt==0:
			amt=1
		#setattr(model, str(i)+"_"+str(amt)+"_constr_more", Constraint(rule=model.amt[i] >= amt+1))
		#setattr(model, str(i)+"_"+str(amt)+"_constr_less", Constraint(rule=model.amt[i] <= amt-1))
		model.amt[i].fix(0)
		return model

	def build_autoplan_week_model(self, 
						food_df, 
						requirements_dict, 
						food_max,
						n_snack,
						global_m,
						src_constr_dict,
						incl_dict,
						sides_dict,
						meal_food_tup,
						meals_idx_tup,
						days,
						leftover_dict
						):
		"""
		TODO - modify requirements_dict / nut cols
		Returns the fully build opt model. 
		Optimization inputs: 
		NONE OF THESE SHOULD BE ALTERED IN THIS FUNCTION
			* opt_input_df - data
			* requirements_dict - dictionary with day as key and nutrients df (nutrient requirements) dict as value
			* food_max - max number of foods
			* n_snack - maximum number of snacks
			* global_m - m for big "M". Must be bigger than food_max
			* src_constr_dict - dictionary that indicates whether optimization for a given (day, meal) tuple should \
						be standalone ('sa'), by dish ('bd') or disjunct ('dj')
			* incl_dict - dictionary indicating if a (day, meal) tuple should be included in optimization. Exists \
						in case of insufficient data
			* sides_dict - min and max number of sides per meal
		"""
		has_dj = False
		# Model Create and Index
		model = ConcreteModel()
		# Indices
		access_df = food_df[['access_idx']]
		full_I_dict = access_df['access_idx'].to_dict()
		access_df.index = access_df['access_idx']
		access_df = access_df.assign(full_I=range(len(access_df)))
		access_dict = access_df['full_I'].to_dict()
		model.access_idx = Set(initialize=access_df.index)
		model.full_I = Set(initialize=food_df.index) # used for objective function only
		# Params
		model.access_idx_lkup = Param(model.access_idx, initialize=access_dict) # To lookup the i based on the access_idx
		model.full_I_lkup = Param(model.full_I, initialize=full_I_dict) # To lookup the access_idx based on the i. For parsing solves
		# Sub-indeces of Full_I
		# Going to loop through meal_idx_tup and use setattr
		for tup in meals_idx_tup:
			if incl_dict[tup] and tup[1] != 'Snack':
				# Setting individual index
				setattr(model,tup[0]+"_"+tup[1], Set(initialize=food_df[(food_df['day']==tup[0])&(food_df['meal']==tup[1])].index))
				if src_constr_dict[tup]=='sa':
					setattr(model, tup[0]+"_"+tup[1]+"_wm",Set(initialize=food_df[(food_df['day']==tup[0])&\
		                                                                          (food_df['meal']==tup[1])&\
		                                                                         (food_df['dish_num']=='Whole Meals')].index))
				elif src_constr_dict[tup]=='bd':
					setattr(model, tup[0]+"_"+tup[1]+"_mc",Set(initialize=food_df[(food_df['day']==tup[0])&\
		                                                                          (food_df['meal']==tup[1])&\
		                                                                         (food_df['dish_num']=='Main Courses')].index))
					setattr(model, tup[0]+"_"+tup[1]+"_si",Set(initialize=food_df[(food_df['day']==tup[0])&\
		                                                                          (food_df['meal']==tup[1])&\
		                                                                         (food_df['dish_num']=='Sides')].index))
				else:
					setattr(model, tup[0]+"_"+tup[1]+"_wm",Set(initialize=food_df[(food_df['day']==tup[0])&\
		                                                                          (food_df['meal']==tup[1])&\
		                                                                         (food_df['dish_num']=='Whole Meals')].index))
					setattr(model, tup[0]+"_"+tup[1]+"_mc",Set(initialize=food_df[(food_df['day']==tup[0])&\
		                                                                          (food_df['meal']==tup[1])&\
		                                                                         (food_df['dish_num']=='Main Courses')].index))
					setattr(model, tup[0]+"_"+tup[1]+"_si",Set(initialize=food_df[(food_df['day']==tup[0])&\
		                                                                          (food_df['meal']==tup[1])&\
		                                                                         (food_df['dish_num']=='Sides')].index))
			elif incl_dict[tup] and tup[1] == 'Snack':
				setattr(model,tup[0]+"_"+tup[1], Set(initialize=food_df[(food_df['day']==tup[0])&\
		                                                                (food_df['meal']==tup[1])].index))
		"""
		Model Params
		"""
		model.amt_ub = Param(model.full_I, initialize=food_df[['max_servings']].to_dict('dict')['max_servings'])
		"""
		Creating Variables
		"""
		model.ind = Var(model.full_I, within=Binary)
		model.amt = Var(model.full_I, within=NonNegativeIntegers, bounds=(0,food_max))
		# Creating Constraints
		# Set A Global Big M constraint so that ind is tied to amt
		def m(model, i):
			return model.amt[i] <= model.ind[i] * global_m
		def use_ind(model, i):
			return model.ind[i] <= model.amt[i]

		model.m_items = Constraint(model.full_I, rule=m)
		model.use_m = Constraint(model.full_I, rule=use_ind)

		"""
		Don't repeat accross days
		"""
		#for tup in meal_food_tup.itertuples():
		for tup in meal_food_tup:
			"""
			Does not include meals
			"""
			# print(tup)
			# idx = food_df[(food_df['fd_type']=='food')&(food_df['unique_id']==tup[1])].index
			# setattr(model, str(tup[1])+"_non_rep", Constraint(expr=sum([model.ind[m] for m in idx])<=tup[2])) # Sets all to '2' which is highly infeasible

			idx = food_df[(food_df['meal']==tup[0])&(food_df['fd_type']==tup[1])&(food_df['unique_id']==tup[2])].index
			setattr(model, tup[0]+tup[1]+str(tup[2])+"_non_rep", Constraint(expr=sum([model.ind[m] for m in idx])<=2)) 
		
		"""
		Disjunction
		"""
		for tup in meals_idx_tup: # Can combine with above loop after getting this down
			if incl_dict[tup] and tup[1] != 'Snack':        
				if src_constr_dict[tup]=='sa':
					setattr(model, tup[0]+"_"+tup[1]+"_sel_wm", 
						Constraint(expr=sum([model.ind[m] for m in getattr(model,tup[0]+"_"+tup[1]+"_wm")])==1))
				elif src_constr_dict[tup]=='bd':
					setattr(model,tup[0]+"_"+tup[1]+"_sel_mc", 
						Constraint(expr=sum([model.ind[m] for m in getattr(model,tup[0]+"_"+tup[1]+"_mc")])==1))
					setattr(model,tup[0]+"_"+tup[1]+"_sel_si", 
						Constraint(expr=inequality(sides_dict['br']['min'],sum([model.ind[m] for m in getattr(model,
		                                                                                    tup[0]+"_"+tup[1]+"_si")]))))
				else:
					setattr(model,tup[0]+"_"+tup[1]+"_sel_sa", 
						Disjunct())
					setattr(getattr(model,tup[0]+"_"+tup[1]+"_sel_sa"),'c1', 
						Constraint(expr=sum([model.ind[m] for m in getattr(model,tup[0]+"_"+tup[1]+"_wm")])==1))
					setattr(getattr(model,tup[0]+"_"+tup[1]+"_sel_sa") ,'c2',
						Constraint(expr=sum([model.ind[m] for m in getattr(model,tup[0]+"_"+tup[1]+"_mc") ])==0))
					setattr(getattr(model,tup[0]+"_"+tup[1]+"_sel_sa"),'c3',
						Constraint(expr=sum([model.ind[m] for m in getattr(model,tup[0]+"_"+tup[1]+"_si") ])==0))
					setattr(model,tup[0]+"_"+tup[1]+"_sel_bd", 
						Disjunct())
					setattr(getattr(model,tup[0]+"_"+tup[1]+"_sel_bd"),'c1',
						Constraint(expr=sum([model.ind[m] for m in getattr(model,tup[0]+"_"+tup[1]+"_wm") ])==0))
					setattr(getattr(model, tup[0]+"_"+tup[1]+"_sel_bd"),'c2',
						Constraint(expr=sum([model.ind[m] for m in getattr(model,tup[0]+"_"+tup[1]+"_mc") ])==1))
					setattr(getattr(model,tup[0]+"_"+tup[1]+"_sel_bd"),'c3',
						Constraint(expr=inequality(sides_dict[tup[1]]['min'],sum([model.ind[m] for m in getattr(model, 
						tup[0]+"_"+tup[1]+"_si" )]),sides_dict[tup[1]]['max'])))
					setattr(model,tup[0]+"_"+tup[1]+"c",Disjunction(expr=[getattr(model,tup[0]+"_"+tup[1]+"_sel_sa" ), 
						getattr(model,tup[0]+"_"+tup[1]+"_sel_bd")]))
					has_dj = True
			elif incl_dict[tup] and tup[1] == 'Snack':
				# Snack Amount Constraints
				setattr(model, tup[0]+"_"+tup[1]+"_ind_n",Constraint(expr=sum([model.ind[m] for m in getattr(model,
					tup[0]+"_"+tup[1])])<=n_snack) )
		# Disjunctive Transformation
		if has_dj:
			trnsfrm = TransformationFactory('gdp.bigm') # Toggle chull bigm
			trnsfrm.apply_to(model)

		# Amount max
		def amt_bounds(model,i):
			return model.amt[i] <= model.amt_ub[i]
		model.amt_bounds = Constraint(model.full_I, rule=amt_bounds)
		# Nutritional bounds  
		for day in days:
			if day in leftover_dict:
				setattr(model, day+"_index", Set(initialize=food_df[(food_df['day']==day)|\
					((food_df['day']==leftover_dict[day]['orig_day'])&\
					(food_df['meal']==leftover_dict[day]['orig_meal']))].index))
			else:
				setattr(model, day+"_index", Set(initialize=food_df[(food_df['day']==day)].index))
			# Will need to also change food_df_dict going forward for different days that already have something planned
			# Set Index N
			nutrient_df = pd.DataFrame(requirements_dict[day])
			nut_cols = list(nutrient_df.columns.values)
			setattr(model, day+"_N", Set(initialize=nut_cols)) 
			food_df_dict = food_df[['prob_r']+nut_cols].to_dict('list')
			setattr(model, day+"_bounds", Param(getattr(model,day+"_N"), initialize=nutrient_df[nut_cols].to_dict('list'))) 
			
			def ml_bounds(model, n):
				return (getattr(model, day+"_bounds")[n][0], sum([food_df_dict[n][i]* model.amt[i] for i in getattr(model,day+"_index")]), 
					getattr(model, day+"_bounds")[n][1])
			setattr(model, day+"_nutr_bounds", Constraint(getattr(model,day+"_N"), rule=ml_bounds))

		# if len(access_idx_list) >0:
		# 	for access_idx in access_idx_list:
		# 		if access_idx in model.access_idx_lkup:
		# 			i = model.access_idx_lkup[access_idx]
		# 			model.ind[i].fix(0)
		# 			model.amt[i].fix(0)
		# Calorie Minimum - not sure if necessary at all - can include calories in bounds above??
		# def cal_min(model):
		#     return  sum([food_df_dict['calories'][i]*model.amt[i] for i in model.full_I]) >= nutrient_df['calories'][0]
		# model.cal_bounds = Constraint(expr=cal_min(model))
		# Per-meal Calorie Minimum - GOING TO SKIP FOR NOW. Pretty marginal
		# if incl_dict['br']:
		#     def br_min(model):
		#             return (ml_min_list[0], sum([food_df_dict['calories'][i]*model.amt[i] for i in model.br]), nutrient_df['calories'][1]-ml_min_list[1]-ml_min_list[2])
		#     model.br_min_const = Constraint(expr=br_min(model))
		# if incl_dict['lu']:
		#     def lu_min(model):
		#         return  (ml_min_list[1], sum([food_df_dict['calories'][i]*model.amt[i] for i in model.lu]), nutrient_df['calories'][1]-ml_min_list[0]-ml_min_list[2])
		#     model.lu_min_const = Constraint(expr=lu_min(model))   
		# if incl_dict['di']:
		#     def di_min(model):
		#         return (ml_min_list[2],sum([food_df_dict['calories'][i]*model.amt[i] for i in model.di]), nutrient_df['calories'][1]-ml_min_list[0]-ml_min_list[1])
		#     model.di_min_const = Constraint(expr=di_min(model))
		#model.excl_amt = ConstraintList()
		# Objective
		def tgt_obj(model):
			return  sum_product(food_df_dict['prob_r'], model.amt, index=model.full_I)
		model.obj = Objective(rule=tgt_obj)
		# Solution
		return model

	def set_opt_variables(self, opt_input_df, days_list, meals_idx_tup):
		"""
		Sets all variables to feed into optimization
		Optimization variables returned here :
			* food_max - max number of foods
			* global_m - m for big "M". Must be bigger than food_max
			* meal_food_tup - tuple with each unique combination of meal and food_id. Used to stop repeating of foods
			* src_constr_dict - dictionary that indicates whether optimization for a given (day, meal) tuple should \
						be standalone ('sa'), by dish ('bd') or disjunct ('dj')
			* incl_dict - dictionary indicating if a (day, meal) tuple should be included in optimization. Exists \
						in case of insufficient data
		"""
		food_max = max(opt_input_df['max_servings'])
		global_m = food_max + 3
		#meal_food_tup = opt_input_df[opt_input_df['fd_type']=='food'][['unique_id', 'max_num_per_week']].drop_duplicates()
		meal_food_tup = [tuple(x) for x in opt_input_df[~opt_input_df['meal'].isin(['Snack', 'Breakfast'])][['meal','fd_type','unique_id']].drop_duplicates().values]
		# print(meal_food_tup)
		src_constr_dict = {}
		incl_dict = {}
		for tup in meals_idx_tup:
		    incl_dict[tup] = True
		    if tup[1] != 'Snack':
		        loop_df = opt_input_df[(opt_input_df['day']==tup[0])&(opt_input_df['meal']==tup[1])]
		        wh = 'Whole Meals' in loop_df['dish_num'].values
		        si = 'Sides' in loop_df['dish_num'].values
		        mc = 'Main Courses' in loop_df['dish_num'].values
		        if wh and (not(si) or not(mc)):
		            src_constr_dict[tup] = 'sa'
		            opt_input_df = opt_input_df.drop(opt_input_df[(opt_input_df['day']==tup[0])&(opt_input_df['meal']==tup[1])&(opt_input_df['dish_num'].isin(['Main Courses', 'Sides']))].index)
		            opt_input_df.reset_index(inplace=True,drop=True)
		        elif not(wh) and (si and mc):
		            src_constr_dict[tup] = 'bd'
		            opt_input_df = opt_input_df.drop(opt_input_df[(opt_input_df['day']==tup[0])&(opt_input_df['meal']==tup[1])&(opt_input_df['dish_num'].isin(['Main Courses', 'Sides']))].index)
		            opt_input_df.reset_index(inplace=True,drop=True)
		        elif wh and si and mc:
		            src_constr_dict[tup] = 'dj'
		        else:
		            incl_dict[tup]=False
		            src_constr_dict[tup] = 'sa'

		return food_max, global_m, meal_food_tup , src_constr_dict, incl_dict

	def build_opt_dataset(self,menus_list, food_df):
		"""
		Builds the dataframe to pass into optimization.
			* builds a per day/meal df from the queried food_df
			* calculates optimization objective 'prob_r'
			* fills na values appropriately
		# TODO - test this design against other data structure that passes a dictionary of meals /
		instead of list of menus. Tradeoff may be in difficulty of building in REACT vs savings here
		"""
		leftover_dict = {}
		opt_input_df = pd.DataFrame()
		for menu_dict in menus_list:
			for meal in menu_dict['meals']:
				for menu in meal['menus']:
					if menu['type']=='leftovers':
						leftover_dict[menu_dict['day']] = {'meal':meal['meal'],'orig_meal':menu['meal'],'orig_day':menu['day']}
					else:
						loop_df = food_df[(food_df['menu_type']==menu['type'])&\
										  (food_df['menu_id']==menu['id'])]
						loop_df['meal'] = meal['meal']
						loop_df = loop_df.assign(day=menu_dict['day'])
						opt_input_df = opt_input_df.append(loop_df)

		opt_input_df = opt_input_df.reset_index(drop=True)
		opt_input_df['last_view'] = opt_input_df['last_view'].fillna(datetime.date(2018,1,1))
		opt_input_df['last_view'] = pd.to_datetime(opt_input_df['last_view'])
		opt_input_df['last_use'] = opt_input_df['last_use'].fillna(datetime.date(2018,1,1))
		opt_input_df['last_use'] = pd.to_datetime(opt_input_df['last_use'])
		opt_input_df['max_servings'] = opt_input_df['max_servings'].fillna(2)
		opt_input_df = opt_input_df.fillna(0)
		opt_input_df = opt_input_df.assign(access_idx=opt_input_df['unique_id'].astype(str)+"_"+opt_input_df['fd_type']+"_"+opt_input_df['day']+"_"+opt_input_df['meal']+"_"+opt_input_df['dish_num']+"_"+opt_input_df['serving_size_val'].astype(str))
		#opt_input_df = opt_input_df.set_index(opt_input_df['unique_id'].astype(str)+opt_input_df['fd_type']+opt_input_df['day']+opt_input_df['meal']+opt_input_df['dish_num'], drop=True)
		prob_r = (1-(opt_input_df['user_total_uses']+0.001)/(opt_input_df['viewed']+0.002))*0.3 \
				 + (5 -opt_input_df['user_star_rating'])*0.3 \
				 + np.random.rand(len(opt_input_df))*0.75 \
				 + 1/(np.maximum([0.5]*len(opt_input_df), opt_input_df['user_total_uses']))*0.3 \
				 + (1/(((datetime.date.today()-opt_input_df['last_view'].dt.date).dt.days)+0.5))*0.1 \
				 + (1/(((datetime.date.today()-opt_input_df['last_use'].dt.date).dt.days)+0.5))*0.25
		opt_input_df = opt_input_df.assign(prob_r = prob_r)
		return opt_input_df, leftover_dict

	def build_just_leftover_dict(self, menus_list):
		"""
		Builds just a leftover dict if we don't also want to build the opt dataset
		"""
		leftover_dict = {}
		for menu_dict in menus_list:
			for meal in menu_dict['meals']:
				for menu in meal['menus']:
					if menu['type']=='leftovers':
						leftover_dict[menu_dict['day']] = {'meal':meal['meal'],'orig_meal':menu['meal'],'orig_day':menu['day']}
		return leftover_dict

	def prep_query_params(self,menus_list):
		"""
		Cycles through database and queries tag, restaurant and menu datasets
		"""
		tag_id_list = [0]
		rest_id_list = [0]
		menu_id_list = [0]
		meal_type_list = []
		meals_idx_tup = []
		days_list = []
		has_menu = False
		has_tag = False
		has_rest = False

		for menu_dict in menus_list:
			"""
			Loop through menus_dict and creates data structures necessary for building the optimization inputs. 
			Includes:
				* tag_id_list, rest_id_list, menu_id_list - unique lists of ids for each query
				* meals_idx_tup - list of tuples for each combination of day, meal
				* days_list - unique list of each day in the dataset
				* has_menu, has_tag, has_rest flags - flags to determine if queries to each db is necessary
			"""
			for meal in menu_dict['meals']:
				days_list.append(menu_dict['day'])
				meals_idx_tup.append((menu_dict['day'], meal['meal']))
				for menu in meal['menus']:
					if menu['type'] == 'menu':
						has_menu = True
						menu_id_list.append(menu['id'])
						if meal['meal'] not in meal_type_list:
							meal_type_list.append(meal['meal'])
					elif menu['type'] == 'tag':
						has_tag = True
						tag_id_list.append(menu['id'])
					elif menu['type'] == 'restaurant':
						has_rest = True
						rest_id_list.append(menu['id'])
					else:
						pass
		"""
		Alternative shape - 
		"""

		# Make Id Lists Unique
		tag_id_tup = tuple(set(tag_id_list))
		rest_id_tup = tuple(set(rest_id_list))
		menu_id_tup = tuple(set(menu_id_list))
		return tag_id_tup, rest_id_tup, menu_id_tup, meals_idx_tup, list(set(days_list))

	def query_food_df(self, connection, params, qry):
		"""
		Params:
			* user_id
			* week_start_dt
			* week_end_dt
			* menu_id_tup
			* tag_id_tup
			* rest_id_tup
		"""
		return_df = pd.read_sql(sql=qry, params=params, con=connection, parse_dates=['last_view'])
		return return_df

	def get_prob_r_coeffs_dict(self, connection):
		"""
		Queries coefficients for 'probability to reject' calculation. Return with food coeffs on the first row and meal coeffs on the second
		"""
		qry= """
			SELECT
				item_type,
				viewed,
				removed,
				total_uses,
				last_view,
				last_use
			FROM core_probrejectcoefficients
			ORDER BY item_type DESC
		"""
		prob_r_df = pd.read_sql(sql=qry, con=connection)
		return prob_r_df.to_dict('list')

	def user_reqs_qry(self):
		"""
		Queries user reqs
		"""
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

	def all_menu_opts_qry(self):
		"""
		Query that combines the menu queries for each tag, rest, and menu id list
		Query parameters:
			* user_id - id of the user. Used for building blocks of 'prob_r' target variable
			* menu_id_tup - id of every menu to be queried (TUPLE)
			* week_start_dt - earliest date to include in exclusion check
			* week_end_dt - latest date to include in exclusion check
			* tag_id_tup - id of every tag to be queried via standalone select (TUPLE)
			* rest_id_tup - id of every restaurant to be queried via standalone select (TUPLE)
		"""
		return"""		
			SELECT
			  fa.meal_id as unique_id,
			  cast('meal' as char(4)) as fd_type,
			  m.meal_type as meal,
			  m.dish_num as dish_num,
			  'menu' as menu_type,
			  m.prefmenu_id as menu_id,
			  pr.viewed,
			  pr.user_total_uses,
			  pr.user_star_rating,
			  coalesce(pr.last_use, cast('2018-01-01' as date)) as last_use,
			  pr.removed,
			  pr.dislike_ind,
			  coalesce(pr.last_view, cast('2018-01-01' as date)) as last_view,
			  pr.max_servings,
			  cast(1 as int) as max_num_per_week,
			  cast(1 as int) as serving_size_val,
			  sum(f.calories*(fa.amt/fa.amount_divisor)) as calories,
			  sum(f.protein_g *(fa.amt/fa.amount_divisor)) as protein_g,
			  sum(f.fat_g *(fa.amt/fa.amount_divisor)) as fat_g,
			  sum(f.carb_g*(fa.amt/fa.amount_divisor)) as carb_g,
			  sum(f.saturated_fat_g*(fa.amt/fa.amount_divisor)) as saturated_fat_g,
			  sum(f.fiber_g*(fa.amt/fa.amount_divisor)) as fiber_g, 
			  sum(f.sugar_g*(fa.amt/fa.amount_divisor)) as sugar_g, 
			  sum(f.sodium_mg*(fa.amt/fa.amount_divisor)) as sodium_mg, 
			  sum(f.cholesterol_mg*(fa.amt/fa.amount_divisor)) as cholesterol_mg,
			  sum(f.calcium_mg*(fa.amt/fa.amount_divisor)) as calcium_mg,
			  sum(f.iron_mg*(fa.amt/fa.amount_divisor)) as iron_mg,
			  sum(f.vit_a_mcg*(fa.amt/fa.amount_divisor)) as vit_a_mcg,
			  sum(f.vit_c_mg*(fa.amt/fa.amount_divisor)) as vit_c_mg
		FROM plan_meal p

		JOIN plan_food_amount fa 
			ON p.id = fa.meal_id

		JOIN food_foods f 
		    ON fa.food_id = f.food_key

		JOIN core_mealpreferences m
			ON p.id = m.meal_id
			AND p.meal_type = m.meal_type

  		LEFT JOIN core_UserProbRejectMeal pr 
		    ON p.id = pr.meal_id
		    AND pr.user_id = %(user_id)s

		WHERE  m.prefmenu_id IN %(menu_id_list)s
			AND not exists
			  (
			    SELECT
			    1
			    FROM core_excludefoods excl
			    WHERE excl.food_id = f.food_key
			      AND excl.user_id = pr.user_id
			      AND excl.start_dt <= %(week_start_dt)s and excl.end_dt >= %(week_end_dt)s
			  )
		GROUP BY fa.meal_id, m.meal_type,m.dish_num,cast('menu' as char(4)), m.prefmenu_id, 
			pr.viewed, pr.user_total_uses, pr.user_star_rating,coalesce(pr.last_use, cast('2018-01-01' as date)) ,
			pr.removed, pr.dislike_ind,coalesce(pr.last_view, cast('2018-01-01' as date)), pr.max_servings, cast(1 as int),cast(1 as int)

		UNION
		/* All foods from menus */
		SELECT
			f.food_key  as unique_id,
			cast('food' as char(4)) as fd_type,
			m.meal_type as meal,
			m.dish_num,
			'menu' as menu_type,
			m.prefmenu_id as menu_id,
			pr.viewed,
			pr.user_total_uses,
			pr.user_star_rating,
			coalesce(pr.last_use, cast('2018-01-01' as date)) as last_use,
			pr.removed,
			pr.dislike_ind,
			coalesce(pr.last_view, cast('2018-01-01' as date)) as last_view,
			COALESCE(pr.max_servings, f.max_servings) as max_servings,
			pr.max_num_per_week,
			f.serving_size_val,
			f.calories,
			f.protein_g,
			f.fat_g,
			f.carb_g,
			f.saturated_fat_g,
			f.fiber_g, 
			f.sugar_g, 
			f.sodium_mg, 
			f.cholesterol_mg,
			f.calcium_mg,
			f.iron_mg,
			f.vit_a_mcg,
			f.vit_c_mg
		FROM core_foodpreferences m

		JOIN food_foods f 
			ON m.food_id = f.food_key 

		LEFT JOIN core_userprobrejectfood pr 
			ON f.food_key = pr.food_id
			AND pr.user_id = %(user_id)s

		WHERE  m.prefmenu_id IN %(menu_id_list)s
			AND not exists
			  (
			    SELECT
			    1
			    FROM core_excludefoods excl
			    WHERE excl.food_id = f.food_key
			      AND excl.user_id = pr.user_id
			      AND excl.start_dt <= %(week_start_dt)s and excl.end_dt >= %(week_end_dt)s
			  )
		UNION
		/* all foods from restaurants from menus*/
		SELECT
			f.food_key  as unique_id,
			cast('food' as char(4)) as fd_type,
			m.meal_type as meal,
			m.dish_num,
			'menu' as menu_type,
			m.prefmenu_id as menu_id,
			pr.viewed,
			pr.user_total_uses,
			pr.user_star_rating,
			coalesce(pr.last_use, cast('2018-01-01' as date)) as last_use,
			pr.removed,
			pr.dislike_ind,
			coalesce(pr.last_view, cast('2018-01-01' as date)) as last_view,
			COALESCE(pr.max_servings, f.max_servings) as max_servings,
			pr.max_num_per_week,
			f.serving_size_val,
			f.calories,
			f.protein_g,
			f.fat_g,
			f.carb_g,
			f.saturated_fat_g,
			f.fiber_g, 
			f.sugar_g, 
			f.sodium_mg, 
			f.cholesterol_mg,
			f.calcium_mg,
			f.iron_mg,
			f.vit_a_mcg,
			f.vit_c_mg

		FROM core_restaurantpreferences m

		JOIN food_foods f 
			ON m.restaurant_id = f.restaurant_id

		LEFT JOIN core_userprobrejectfood pr 
			ON pr.user_id = %(user_id)s
			AND f.food_key = pr.food_id

		WHERE m.prefmenu_id IN %(menu_id_list)s
			AND not exists
			  (
			    SELECT
			    1
			    FROM core_excludefoods excl
			    WHERE excl.food_id = f.food_key
			      AND excl.user_id = pr.user_id
			      AND excl.start_dt <= %(week_start_dt)s and excl.end_dt >= %(week_end_dt)s
			  )
		UNION
			/* all foods from tags from menu */
		SELECT
			f.food_key  as unique_id,
			cast('food' as char(4)) as fd_type,
			m.meal_type as meal,
			m.dish_num,
			'menu' as menu_type,
			m.prefmenu_id as menu_id,
			pr.viewed,
			pr.user_total_uses,
			pr.user_star_rating,
			coalesce(pr.last_use, cast('2018-01-01' as date)) as last_use,
			pr.removed,
			pr.dislike_ind,
			coalesce(pr.last_view, cast('2018-01-01' as date)) as last_view,
			COALESCE(pr.max_servings, f.max_servings) as max_servings,
			pr.max_num_per_week,
			f.serving_size_val,
			f.calories,
			f.protein_g,
			f.fat_g,
			f.carb_g,
			f.saturated_fat_g,
			f.fiber_g, 
			f.sugar_g, 
			f.sodium_mg, 
			f.cholesterol_mg,
			f.calcium_mg,
			f.iron_mg,
			f.vit_a_mcg,
			f.vit_c_mg

		FROM core_foodtagpreferences m

		JOIN food_taggedfoods t
			ON m.tag_id = t.foodtag_id

		JOIN food_foods f 
			ON t.food_id = f.food_key

		LEFT JOIN core_userprobrejectfood pr 
			ON pr.user_id = %(user_id)s
			AND f.food_key = pr.food_id

		WHERE m.prefmenu_id IN %(menu_id_list)s
			AND not exists
			  (
			    SELECT
			    1
			    FROM core_excludefoods excl
			    WHERE excl.food_id = f.food_key
			      AND excl.user_id = pr.user_id
			      AND excl.start_dt <= %(week_start_dt)s and excl.end_dt >= %(week_end_dt)s
			  )
		UNION 
		/* Standalone food tag query */
		SELECT
			f.food_key  as unique_id,
			cast('food' as char(4)) as fd_type,
			'placeholder' as meal,
			COALESCE(pr.default_dish_num, f.default_dish_num) as dish_num,
			'tag' as menu_type, 
			t.id as menu_id,
			pr.viewed,
			pr.user_total_uses,
			COALESCE(pr.user_star_rating, f.star_rating) as user_star_rating,
			coalesce(pr.last_use, cast('2018-01-01' as date)) as last_use,
			pr.removed,
			pr.dislike_ind,
			coalesce(pr.last_view, cast('2018-01-01' as date)) as last_view,
			COALESCE(pr.max_servings, f.max_servings) as max_servings,
			pr.max_num_per_week,
			f.serving_size_val,
			f.calories,
			f.protein_g,
			f.fat_g,
			f.carb_g,
			f.saturated_fat_g,
			f.fiber_g, 
			f.sugar_g, 
			f.sodium_mg, 
			f.cholesterol_mg,
			f.calcium_mg,
			f.iron_mg,
			f.vit_a_mcg,
			f.vit_c_mg

		FROM food_taggedfoods t

		JOIN food_foods f 
			ON t.food_id = f.food_key

		LEFT JOIN core_userprobrejectfood pr 
			ON f.food_key = pr.food_id
			AND pr.user_id = %(user_id)s

		WHERE t.foodtag_id IN %(tag_id_list)s
			AND NOT EXISTS
			(
				SELECT
				1
				FROM core_excludefoods excl
				WHERE excl.food_id = pr.food_id
				AND excl.user_id = pr.user_id
				AND excl.start_dt <= %(week_start_dt)s and excl.end_dt >= %(week_end_dt)s
			)
		UNION 
		/* Queries standalone restaurant options */
		SELECT
			f.food_key  as unique_id,
			cast('food' as char(4)) as fd_type,
			'placeholder' as meal,
			COALESCE(pr.default_dish_num, f.default_dish_num) as dish_num,
			'restaurant' as menu_type, 
			f.restaurant_id as menu_id,
			pr.viewed,
			pr.user_total_uses,
			COALESCE(pr.user_star_rating, f.star_rating) as user_star_rating,
			coalesce(pr.last_use, cast('2018-01-01' as date)) as last_use,
			pr.removed,
			pr.dislike_ind,
			coalesce(pr.last_view, cast('2018-01-01' as date)) as last_view,
			COALESCE(pr.max_servings, f.max_servings) as max_servings,
			pr.max_num_per_week,
			f.serving_size_val,
			f.calories,
			f.protein_g,
			f.fat_g,
			f.carb_g,
			f.saturated_fat_g,
			f.fiber_g, 
			f.sugar_g, 
			f.sodium_mg, 
			f.cholesterol_mg,
			f.calcium_mg,
			f.iron_mg,
			f.vit_a_mcg,
			f.vit_c_mg

		FROM  food_foods f 

		LEFT JOIN core_userprobrejectfood pr 
		ON f.food_key = pr.food_id
		AND pr.user_id = %(user_id)s

		WHERE   f.restaurant_id IN %(rest_id_list)s
		AND NOT EXISTS
		  (
		    SELECT
		    1
		    FROM core_excludefoods excl
		    WHERE excl.food_id = f.food_key
		      AND excl.user_id = pr.user_id
		      AND excl.start_dt <= %(week_start_dt)s and excl.end_dt >= %(week_end_dt)s
		  )"""