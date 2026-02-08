import pandas as pd 
import json
import time
import sys
import pyodbc
import os
sys.path.append("../..")
from timeit import default_timer as timer
#from django.db.models.expressions import connection
from autoplanner.autoplan_week import WeekAutoPlanner
from autoplanner.test.test_odbc_style_query import all_menu_opts_qry_odbc, query_datasets
from secrets import *

def timing(f):
    def wrapper(*args, **kwargs):
        start = timer()
        result = f(*args, **kwargs)
        end = timer()
        print(f'Elapsed time for {f.__name__}: {end-start}')
        return result
    return wrapper

@timing
def query_datasets_timed(connection,user_id,menus_list, week_start_dt, week_end_dt):
	return query_datasets(connection,user_id,menus_list, week_start_dt, week_end_dt)

@timing
def build_opt_dataset_timed(obj, menus_list,food_df):
	return obj.build_opt_dataset(menus_list, food_df)

@timing
def set_opt_variables_timed(obj,opt_input_df, days_list, meals_idx_tup):
	return obj.set_opt_variables(opt_input_df, days_list, meals_idx_tup)

@timing
def build_autoplan_week_model_timed(obj,opt_input_df,requirements_dict,food_max,n_snack,global_m,
	 	src_constr_dict,incl_dict,sides_dict,meal_food_tup, meals_idx_tup, days_list, leftover_dict):
	return obj.build_autoplan_week_model(opt_input_df,requirements_dict,food_max,n_snack,global_m,
	 	src_constr_dict,incl_dict,sides_dict,meal_food_tup, meals_idx_tup, days_list, leftover_dict)

@timing
def solve_weekplan_model_timed(obj,solver_rel_path, model):
	return obj.solve_weekplan_model(solver_rel_path, model)

@timing
def parse_weekplan_model_results_timed(obj, model, opt_input_df, leftover_dict):
	return obj.parse_weekplan_model_results(model, opt_input_df, leftover_dict)

if __name__ == '__main__':
	os.environ['DJANGO_SETTINGS_MODULE'] = 'planyourmeals_api.settings.base'
	#export DJANGO_SETTINGS_MODULE=
	with open('autoplan_week_test_params1.json') as json_file:
		params = json.load(json_file)
	#print()
	connection = pyodbc.connect('DSN=PostgreSQL30;PWD=v2nc3123')
	planner = WeekAutoPlanner(connection=connection, 
								user_id=str(2), 
								requirements_dict=params["params"]["requirements_dict"],
								menus_dict_list=params["params"]["menus_dict_list"],
								week_start_dt=params["params"]["week_start_dt"],
								week_end_dt=params["params"]["week_end_dt"],
								n_snack=6,
								solver_rel_path="../../../plm_env/lib/python3.6/site-packages/Cbc-2.9.8/bin/cbc")
	connection = planner.connection
	user_id = planner.user_id 
	requirements_dict = planner.requirements_dict
	menus_list = planner.menus_list
	week_start_dt = planner.week_start_dt
	week_end_dt = planner.week_end_dt
	n_snack = planner.n_snack
	sides_dict = planner.sides_dict
	solver_rel_path = planner.solver_rel_path
	# Query data and set relevant variables
	food_df, meals_idx_tup, days_list = query_datasets_timed(connection,user_id,menus_list, week_start_dt, week_end_dt)
	# Create dataset
	opt_input_df, leftover_dict = build_opt_dataset_timed(planner, menus_list, food_df)
	print(str(len(opt_input_df)))
	# # Set optimization variables
	food_max, global_m, meal_food_tup, src_constr_dict, incl_dict = set_opt_variables_timed(planner,opt_input_df, days_list, meals_idx_tup)
	# # Build_autoplan_week_model
	model = build_autoplan_week_model_timed(planner,opt_input_df,requirements_dict,food_max,n_snack,global_m,
	 	src_constr_dict,incl_dict,sides_dict,meal_food_tup, meals_idx_tup, days_list, leftover_dict)
	# Solve model
	model = solve_weekplan_model_timed(planner,solver_rel_path, model)
	# Parse results
	results_df = parse_weekplan_model_results_timed(planner, model, opt_input_df, leftover_dict)
	results_df.to_csv("C:/Users/J/Desktop/Git_Repositories/planyourmeals_api/autoplanner/test/test_results_df.csv",index=False)

