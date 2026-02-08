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


if __name__ == '__main__':
	os.environ['DJANGO_SETTINGS_MODULE'] = 'planyourmeals_api.settings.base'
	#export DJANGO_SETTINGS_MODULE=
	with open('autoplan_week_test_params3.json') as json_file:
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
								solver_rel_path="../../../plm_env/lib/python3.6/site-packages/Cbc-2.9.8/bin/cbc",
								server_type='prod')
	results1, results2 = planner.solve_and_resolve_weekplan()
	results1.to_csv("C:/Users/J/Desktop/Git_Repositories/planyourmeals_api/autoplanner/test/test_results1.csv",index=False)
	results2.to_csv("C:/Users/J/Desktop/Git_Repositories/planyourmeals_api/autoplanner/test/test_results2.csv",index=False)


