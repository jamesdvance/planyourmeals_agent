from django.shortcuts import render
from django.core.serializers import serialize, deserialize
from django import core
from django.db import models
#from django.db.models import F
from django.db.models.expressions import connection
from django.http import JsonResponse, HttpResponse
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
#from django.views.decorators.csrf import 
# 3rd party
import pandas as pd
import numpy as np
import boto3
import cloudpickle
# for unpickling cloud model
from pyomo.environ import *
from pyomo.opt import SolverFactory
from pyomo.gdp import *
import pyutilib.subprocess.GlobalData
pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False
import json
import datetime
import requests
import logging
#logging.basicConfig(filename='../logs/plan.log',level=logging.ERROR)
from secrets import AK, SAK
# Local apps
from food.models import Foods
from core.models import UserProbRejectMeal, UserProbRejectFood
from plan.models import Meal, Food_Amount, PlanMeal
from plan.serializers import *
# Autoplan class
from autoplanner.autoplan_week import WeekAutoPlanner
from autoplanner.adjust_amounts import AmountAdjuster
from autoplanner.alternatives_engine import AlternativesEngine
# Tasks
from core.tasks import update_viewed_today
# Create your views here.

#	***
# 	CONSTANTS
#	***
ml_cd_dict = {'Breakfast':'br','Lunch':'lu','Dinner':'di','Snack':'sn'}
meals = ['Breakfast','Lunch','Dinner','Snack']
db_to_display_dict = {'calories':'Calories','protein_g':'Protein', 'fat_g':'Fat','carb_g':'Carbs','fiber_g':'Fiber',
						'calcium_mg':'Calcium','iron_mg':'Iron','vit_a_mcg':'Vitamin A','vit_c_mg':'Vitamin C','sugar_g':'Sugar',
						'saturated_fat_g':'Sat. Fat','sodium_mg':'Sodium', 'cholesterol_mg':'Cholesterol'}

#	***
#	SEARCH
#	***
@api_view(['POST'])
def search_foods(request):
	post_data = request.data['params'] # 'Params' from axios request
	search_qry = post_data['search_qry'].lower()
	food_type_grp = post_data['food_type_grp']
	search_results = Foods.objects.filter(food_description__contains=search_qry,food_type_grp__in=food_type_grp)
	serializer = FoodModelSerializer(search_results, many=True)
	return Response(serializer.data)

class FoodSearchView(APIView):
	"""
	Retrieves foods objects joined to alt serving size
	"""
	def post(self,request):
		post_data = request.data['params'] # 'Params' from axios request
		search_qry = post_data['search_qry'].lower()
		food_type_grp = post_data['food_type_grp']
		nth_search = post_data['nth_search']
		exact_search_results = Foods.objects.filter(food_description=search_qry,food_type_grp__in=food_type_grp)\
							.annotate(order=models.Value(0,models.IntegerField()),
								serving_sizes=F('alt_serving_size__serving_sizes'),
								amt=F('serving_size_val'),
								serving_size_idx=models.Value(0,models.IntegerField()))
		like_search_results = Foods.objects.filter(food_description__contains=search_qry,food_type_grp__in=food_type_grp)\
							.annotate(order=models.Value(1, models.IntegerField()),
								serving_sizes=F('alt_serving_size__serving_sizes'),
								amt=F('serving_size_val'),
								serving_size_idx=models.Value(0,models.IntegerField()))
		search_results = exact_search_results.union(like_search_results, all=False).order_by('order')[0:500]
		serializer = FoodSearchSerializer(search_results, many=True)
		# search_results_dict = {str(obj['food_key'])+"_searchResults_"+str(nth_search): obj for obj in serializer.data}
		# search_results_by_id = [str(obj['food_key'])+"_searchResults_"+str(nth_search) for obj in serializer.data]
		search_results_dict = {}
		search_results_by_id = []
		for obj in serializer.data:
			search_results_dict[str(obj['food_key'])+"_searchResults_"+str(nth_search)] = obj
			search_results_by_id.append(str(obj['food_key'])+"_searchResults_"+str(nth_search))
		return Response({'search_results_dict':search_results_dict,'search_results_by_id':search_results_by_id})# unique only
			
@api_view(['POST'])
def search_foods_raw(request):
	"""
	Returns up to 500 results for foods. Contains exact and LIKE results using a raw parameterized SQL query
	"""
	post_data = request.data['params'] # 'Params' from axios request
	search_qry = post_data['search_qry'].lower()
	food_type_grp = post_data['food_type_grp']
	nth_search = post_data['nth_search']
	try: 
		brand = post_data['brand'].lower()
	except:
		brand=False

	brand_qry = """
		SELECT
			concat(f.food_key,'_searchResults_', %(nth_search)s) as drag_key,
			f.*,
			s.serving_sizes,
			CASE WHEN f.food_description = %(search_qry)s THEN 0 ELSE 1 END AS order,
			f.serving_size_val as amt,
			0 as serving_size_idx
		FROM food_foods f
			JOIN food_altservingsize s
				ON f.food_key = s.food_id
		WHERE f.food_description LIKE %(search_qry_like)s
			AND f.food_type_grp in %(food_type_grp)s
			AND f.brand LIKE %(brand_like)s
		ORDER BY CASE WHEN f.food_description = %(search_qry)s THEN 0 ELSE 1 END
		LIMIT 100
	"""
	no_brand_qry="""
		SELECT
			concat(f.food_key,'_searchResults_', %(nth_search)s) as drag_key,
			f.*,
			s.serving_sizes,
			CASE WHEN f.food_description = %(search_qry)s THEN 0 ELSE 1 END AS order,
			f.serving_size_val as amt,
			0 as serving_size_idx
		FROM food_foods f
			JOIN food_altservingsize s
				ON f.food_key = s.food_id
		WHERE f.food_description LIKE %(search_qry_like)s
			AND f.food_type_grp in %(food_type_grp)s
		ORDER BY CASE WHEN f.food_description = %(search_qry)s THEN 0 ELSE 1 END
		LIMIT 100
	"""
	qry_params = {"search_qry":search_qry, "search_qry_like":"%"+search_qry+"%", "food_type_grp":tuple(food_type_grp), 'nth_search':nth_search}
	if brand:
		qry_params['brand_like'] = brand+"%"
		df = pd.read_sql(sql=brand_qry,params=qry_params, con=connection)
	else:
		df = pd.read_sql(sql=no_brand_qry, params=qry_params, con=connection)
	df = df.fillna(0)
	df = df.assign(drag_id=df['food_key'].astype(str)+"_searchResults_"+str(nth_search))
	df_rec = df.to_dict('records') # records is shape [{col->val}, {col->val}]
	#df_rec = df.to_dict('index') # index is shape {idx:{col->val},idx:{col->val}}
	return Response({'search_results_by_id':df_rec})

@api_view(['POST'])
def search_meals(request):
	post_data = request.data['params'] # 'Params' from axios request
	search_qry = post_data['search_qry'].lower()
	nth_search = post_data['nth_search']
	user_added_only = post_data['user_added_only']
	if user_added_only:
		user_add_filter = f" and m.user_id = {request.user.id} "
	else:
		user_add_filter = ""
	qry = """
			SELECT
			  m.id as meal_id,
			  m.mealname,
			  m.cloned_n,
			  concat(m.id, '_searchResults_',%(nth_search)s) as meal_drag_key,
			  concat(f.food_key,'_','searchResults','_meal_',m.id) as drag_id,
			  am.amt,
			  am.serving_size_idx,
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
	
			FROM plan_meal m
			JOIN plan_food_amount am
			  ON m.id = am.meal_id
			JOIN food_foods f
			  ON f.food_key = am.food_id
			JOIN food_altservingsize ss
			  ON f.food_key = ss.food_id
			WHERE m.mealname like %(search_qry_like)s AND m.saved='true' """+user_add_filter+"""
			LIMIT 100;
	"""	
	qry_params = { "search_qry_like":"%"+search_qry+"%",  'nth_search':nth_search} # uses two-side like for meals
	df = pd.read_sql(sql=qry,params=qry_params, con=connection)
	df = df.fillna(0)
	meal_columns = ['meal_id','mealname', 'cloned_n','meal_drag_key']
	if len(df) == 0:
		return Response({'meal_search_results':[]})
	result_df = df.groupby(meal_columns, as_index=False)\
		.apply(lambda x: x.to_dict('records'))\
		.to_frame('foods')\
		.reset_index(level=meal_columns)\
		.to_dict('records')
	return Response({'meal_search_results':result_df})

@api_view(['POST'])
def search_tags(request):
	"""
	Return all foods for a certain tag
	"""
	post_data = request.data['params'] # 'Params' from axios request
	search_qry = post_data['search_qry'].lower()
	nth_search = post_data['nth_search']
	tag_qry="""
		SELECT
			concat(f.food_key,'_searchResults_', %(nth_search)s) as drag_key,
			f.*,
			s.serving_sizes,
			CASE WHEN f.food_description = %(search_qry)s THEN 0 ELSE 1 END AS order,
			f.serving_size_val as amt,
			0 as serving_size_idx
		FROM food_taggedfoods tf
			JOIN food_foodtags ft
				ON tf.id = ft.foodtag_id
			JOIN food_foods f
				ON tf.food_id = f.food_key
			JOIN food_altservingsize s
				ON f.food_key = s.food_id
		WHERE tf.name = %(search_qry)s 
		LIMIT 100
	"""
	qry_params = {"search_qry":search_qry,  'nth_search':nth_search}
	return


@api_view(['POST'])
def search_brands(request):
	pass

#	***
#	PLAN
#	***

class WeekPlan():
	"""
	Breaking convention here. Not using the APIView mixin. The WeekPlan class will be used \
	by different functional views to get or update weekplans. 
	"""
	def __init__(self):
		pass

	def get_weekplan(self,plan_date_tup,week_start_dt, user_id):
		"""
		Inputs:
			* plan_date_tup - tuple of date strings "YYYY-MM-DD"
			* week_start_dt - python datetime object of first date in plan_date_tup
			* user_id - integer representing user_id
		"""
		qry="""
			SELECT
			  p.plan_date,
			  m.mealname,
			  p.meal_type,
			  am.meal_id,
			  am.amt,
			  am.serving_size_idx,
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
			WHERE p.plan_date in %(plan_date_tup)s and p.user_id = %(user_id)s;
		"""
		qry_params = { "plan_date_tup":plan_date_tup, "user_id":user_id}
		df = pd.read_sql(sql=qry, params=qry_params, con=connection)
		if df.empty:
			return {}
		else:
			df = df.fillna(0)
			df['plan_date'] = pd.to_datetime(df['plan_date']).dt.date
			df = df.assign(daynum = (df['plan_date'] - week_start_dt).dt.days)
			df['daynum'] = df['daynum']+1
			df = df.assign(plannum = "day"+df['daynum'].astype(str))
			df = df.assign(drag_id=df['food_key'].astype(str)+"_"+df['plannum']+"_"+df['meal_type'])
			df = df.assign(food_drag_key =df['drag_id'])
			df = df.assign(meal_drag_key=df['meal_id'].astype(str)+"_"+df['plannum']+"_"+df['meal_type'])
			df = df.assign(loading=False)
			day_columns = ['plannum', 'plan_date']
			meal_columns = ['meal_id','mealname','meal_type', 'meal_drag_key','plannum', 'plan_date', 'daynum']
			results_df = df.groupby(meal_columns, as_index=False)\
				.apply(lambda x: x.to_dict('records'))\
				.to_frame('foods_list')\
				.reset_index(level=meal_columns)
			results_idx = pd.MultiIndex.from_tuples(list(zip(list(results_df['plannum']),list(results_df['meal_type']))))
			results_df.index = results_idx
			results_dict = results_df.groupby(level=0)\
					.apply(lambda x: x.xs(x.name).to_dict('index')).to_dict()
			# Add null results. Only need to fill in meals that don't exist, not days
			meals = ['Breakfast','Lunch','Dinner','Snack']
			for plannum in df['plannum'].unique():
				for meal in meals:
					if meal not in results_dict[plannum]:
						results_dict[plannum][meal]=  {
							'meal_id':0,
							'plannum':plannum,
							'daynum':int(plannum[3]),
							'isLoading':False,
							'meal_drag_key':'0_'+plannum+"_"+meal,
							'meal_type':meal,
							'mealname':"Unnamed",
							'plan_date':None,
							'foods_list':[]
						}
			return results_dict

@api_view(['POST'])
def get_range_plan(request):
	"""
	Return full meal plan per date range
	Accepts a list of dates and user id
	"""
	post_data = request.data['params'] # 'Params' from axios request
	date_list = post_data["date_list"]
	week_start_dt = datetime.datetime.strptime(post_data["week_start_dt"],"%Y-%m-%d").date()
	user_id = request.user.id
	weekplan = WeekPlan()
	results = weekplan.get_weekplan(plan_date_tup=tuple(date_list),week_start_dt=week_start_dt, user_id=user_id)
	return Response(results)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_day_plan(request):
	"""
	TODO - rewrite as class-based view. Can also be used by each solve function. And \
	combine with 'update_meal_from_list' for same reason
	Purpose: Return full meal plan per one day
	"""
	post_data = request.data['params'] # 'Params' from axios request
	plan_date = post_data['plan_date']
	plannum = post_data['plannum']
	#plan = PlanMeal.objects.filter(user=request.user, plan_date=plan_date).select_related()
	qry="""
		SELECT
		  concat(f.food_key,'_',%(plannum)s,'_', %(meal_type)s) as drag_key,
		  am.meal_id,
		  am.amt,
		  am.serving_size_idx,
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
		WHERE plan_date = %(plan_date)s AND p.meal_type=%(meal_type)s;
	"""
	result = {}
	for meal_type in meals:
		"""
		Pull the data for each meal
		"""
		qry_params = {"meal_type":meal_type,"plannum":plannum, "plan_date":plan_date}
		df = pd.read_sql(sql=qry,params=qry_params,con=connection)
		df = df.fillna(0)
		df = df.assign(drag_id=df['food_key'].astype(str)+"_"+plannum+"_"+meal_type)
		#result[meal_type] = df.to_dict('records')
		result[meal_type] = {}
		result[meal_type]['foods_list'] = df.to_dict('records')
		if len(result[meal_type]['foods_list']) ==0:
			meal_id = 0
		else:
			meal_id = result[meal_type]['foods_list'][0]['meal_id']
		result[meal_type]['meal_drag_key'] = str(meal_id)+"_"+plannum+"_"+meal_type
	return Response(result)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_meal_from_list(request):
	"""
	Add a full meal to a plan
	"""
	# Parameters
	post_data = request.data['params'] # 'Params' from axios request
	meal_type = post_data['meal_type']
	plan_date = post_data['plan_date']
	foods_list = post_data['foods_list']
	ml_cd = ml_cd_dict[meal_type]
	if plan_date == str(datetime.date.today()):
		update_viewed_today.delay(foods_list, request.user.id) # ASYNC Celery task
	# Check If PlanMeal exists:
	if PlanMeal.objects.filter(user=request.user, meal_type=meal_type,plan_date=plan_date).exists():
		plan = PlanMeal.objects.get(user=request.user,meal_type=meal_type,plan_date=plan_date)
		if not plan.meal_id:
			meal = Meal.objects.create(user=request.user, meal_type=meal_type)
			plan.meal_id = meal.id
			plan.save()
		else:
			meal = Meal.objects.get(id=plan.meal_id)

	else:
		meal = Meal.objects.create(user=request.user, meal_type=meal_type)
		plan = PlanMeal.objects.create(user=request.user,ml_cd=ml_cd,meal_type=meal_type,plan_date=plan_date, meal_id=meal.id)
	# add foods to meal
	Food_Amount.objects.filter(meal_id=meal.id).delete()
	for food_obj in foods_list:
		"""
		Make updates in Food Amount
		"""
		#adj_amt = (float(food_obj['serving_sizes']['ss_amts'][0])*float(food_obj['amt']))/float(food_obj['serving_sizes']['ss_amts'][food_obj['serving_size_idx']])
		adj_amt = float(food_obj['serving_sizes']['ss_amts'][food_obj['serving_size_idx']])
		# Catch instances where food_amount already exists
		if Food_Amount.objects.filter(meal_id=meal.id,food_id=food_obj['food_key']).exists():
			food_am = Food_Amount.objects.get(meal_id=meal.id,food_id=food_obj['food_key'])
			# not doing += to avoid having to convert all to Decimal first (requiring importing another package)
			food_am.amt = float(food_am.amt) + float(food_obj['amt'])*(float(food_obj['serving_sizes']['ss_amts'][food_obj['serving_size_idx']])\
				 /float(food_obj['serving_sizes']['ss_amts'][food_obj['serving_size_idx']]))
			food_am.save()
		else:
			Food_Amount.objects.create(meal_id=meal.id,
							food_id=food_obj['food_key'], 
							amt=food_obj['amt'], 
							serving_size_idx=food_obj['serving_size_idx'],
							amount_divisor=adj_amt)
	return Response({'status':'success'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_week_from_list(request):
	"""
	Update a whole week from the columns state
	"""
	days = ['day1', 'day2', 'day3', 'day4', 'day5', 'day6', 'day7']
	meals = ['Breakfast', 'Lunch', 'Dinner', 'Snack']
	post_data = request.data['params'] # 'Params' from axios request
	columns = post_data['columns']
	days_dict = post_data['days_dict']
	user_id = request.user.id
	for day in days:
		col = columns[day]
		for meal in meals:
			plan_meal,_ = PlanMeal.objects.get_or_create(user_id=request.user.id,meal_type=meal, plan_date=days_dict[day])
			food_amount = Food_Amount.objects.filter(meal_id=plan_meal.meal_id).delete()
			foods_list = col[meal]['foods_list']
			if days_dict[day] == str(datetime.date.today()):
				update_viewed_today.delay(foods_list, request.user.id) # ASYNC Celery task
			for food_obj in foods_list:
				Food_Amount.objects.create(meal_id=plan_meal.meal_id,
							food_id=food_obj['food_key'], 
							amt=food_obj['amt'], 
							serving_size_idx=food_obj['serving_size_idx'],
							amount_divisor=food_obj['serving_sizes']['ss_amts'][food_obj['serving_size_idx']])
	return Response({'status':'success'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_meals(request):
	"""
	Remove all foods from meals in a given list of meals for a given day
	"""
	post_data = request.data['params'] # 'Params' from axios request
	user_id = request.user.id
	meal_type_list = post_data["meal_type_list"]
	plan_date = post_data['plan_date']
	for meal_type in meal_type_list:
		if PlanMeal.objects.filter(user=request.user, meal_type=meal_type, plan_date=plan_date).exists():
			plan_meal = PlanMeal.objects.get(user=request.user, meal_type=meal_type, plan_date=plan_date)
			Food_Amount.objects.filter(meal_id=plan_meal.meal_id).delete()
	return Response({'status':'success'})

def add_to_meal(request):
	"""
	Add a food to a meal
	"""
	return Response({'status':'success'})

def update_meal_ss(request):
	"""
	update serving size amt
	"""
	return Response({'status':'success'})

def remove_from_meal(request):
	"""
	Remove from meal
	"""
	return Response({'status':'success'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_meal(request):
	"""
	Get meal by id
	"""
	post_data = request.data['params'] # 'Params' from axios request
	meal_id = post_data['meal_id']
	meal_qry = """
		SELECT
			*
		FROM plan_meal
		WHERE id=%(meal_id)s
	"""
	params ={'meal_id':meal_id}
	meal_df = pd.read_sql(sql=meal_qry, params=params, con=connection)
	meal_df = meal_df.fillna(0)
	meal_dict = meal_df.to_dict('records')[0]
	meal_foods_qry = """
		SELECT
			  m.id as meal_id,
			  m.mealname,
			  m.cloned_n,
			  am.amt,
			  am.serving_size_idx,
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
		FROM 
			plan_meal m
		JOIN plan_food_amount am
			ON am.meal_id = m.id
		JOIN food_foods f
			ON am.food_id = f.food_key
		JOIN food_altservingsize ss
			ON f.food_key = ss.food_id
		WHERE m.id =%(meal_id)s
	"""
	meal_foods_df = pd.read_sql(sql=meal_foods_qry, params=params, con=connection)
	meal_foods_df = meal_foods_df.fillna(0)
	meal_foods_list = meal_foods_df.to_dict('records')
	return Response({'meal_dict':meal_dict, 'meal_foods_list':meal_foods_list})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_meal(request):
	"""
	Save new meal
	"""
	post_data = request.data['params'] 
	mealname = post_data['mealname'].lower()
	default_meal = post_data['default_meal']
	foods_list = post_data['foods_list']
	new_meal = Meal.objects.create(mealname=mealname, meal_type=default_meal, user_id=request.user.id, saved=True)
	for food in foods_list:
		alt_ss = AltServingSize.objects.get(food_id=food['food_key'])
		adj_amt = alt_ss.serving_sizes['ss_amts'][food['serving_size_idx']]
		new_food_amount = Food_Amount.objects.create(meal_id=new_meal.id, 
					food_id=food['food_key'], 
					amt=food['amt'], 
					serving_size_idx=food['serving_size_idx'],
					amount_divisor=adj_amt)
	return Response({'status':'success'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_meal(request):
	"""
	Edit meal
	"""
	post_data = request.data['params'] 
	meal_id = post_data['meal_id']
	mealname = post_data['mealname']
	default_meal = post_data['default_meal']
	foods_list = post_data['foods_list']
	edited_meal = Meal.objects.get(id=meal_id)  # saved is already true
	Food_Amount.objects.filter(meal_id=meal_id).delete()
	for food in foods_list:
		alt_ss = AltServingSize.objects.get(food_id=food['food_key'])
		adj_amt = alt_ss.serving_sizes['ss_amts'][food['serving_size_idx']]
		new_food_amount = Food_Amount.objects.create(meal_id=meal_id, 
					food_id=food['food_key'], 
					amt=food['amt'], 
					serving_size_idx=food['serving_size_idx'],
					amount_divisor=adj_amt)
	return Response({'status':'success'})

#	***
#	AUTOPLAN
#	***
def diagnose_autoplan_failure():
	pass

def save_weekplan_model(model, user_id):
	s3_client = boto3.client('s3',
		aws_access_key_id=AK,
		aws_secret_access_key=SAK,
	)
	result = s3_client.put_object(Bucket="planyourmealsmodels",Body=model,Key="saved_models/"+str(user_id)+"/saved_model")

def get_weekplan_model(user_id):
	s3 = boto3.resource('s3')
	obj = s3.Object('planyourmealsmodels','saved_models/2/saved_model')
	body = obj.get()['Body'].read()
	return body

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def autoplan_week(request):
	post_data = request.data['params']
	menus_dict_list = post_data['menus_dict_list']
	week_start_dt = post_data['week_start_dt']
	incl_replace = post_data['incl_replace']
	nth_solve = post_data['nth_solve']
	user_id = request.user.id
	# needed for weekautoplanner only
	requirements_dict = post_data['requirements_dict']
	solver_params_dict = post_data['solver_params_dict']
	week_end_dt = post_data['week_end_dt']
	# planner = WeekAutoPlanner(connection=connection, 
	# 							user_id=str(user_id), 
	# 							requirements_dict=requirements_dict,
	# 							menus_dict_list=menus_dict_list
	# 							week_start_dt=week_start_dt,
	# 							week_end_dt=week_end_dt,
	# 							n_snack=6,
	# 							solver_rel_path="../plm_env/lib/python3.6/site-packages/Cbc-2.9.8/bin/cbc",
	# 							solver_params_dict=solver_params_dict) #TODO - get "n-snack" from menu preferences
	# # print("starting solve")
	# if incl_replace and nth_solve==0:
	# 	curr_plan_list = post_data['curr_plan_list']
	# 	n_repl_dict = post_data['n_repl_dict']
	# 	plan_df,model = planner.resolve_weekplan(curr_plan_list, n_repl_dict)
	# elif incl_replace and nth_solve >0:
	# 	curr_plan_list = post_data['curr_plan_list']
	# 	pickled_model = get_weekplan_model(user_id)
	# 	saved_model = cloudpickle.loads(pickled_model)
	# 	plan_df, model = planner.solve_again_weekplan(saved_model, curr_plan_list)
	# else:
	# 	plan_df, model = planner.solve_and_return_weekplan()

	# pickled_model = cloudpickle.dumps(model)
	# save_weekplan_model(pickled_model, user_id) # save to s3
	send_dict= request.data
	send_dict['params']['user_id'] = request.user.id
	if incl_replace and nth_solve==0:
		response = requests.post(url='http://c5_autoplanner.planyourmeals.com/api/resolve_autoplan',json=send_dict)
	elif incl_replace and nth_solve >0:
		response = requests.post(url='http://c5_autoplanner.planyourmeals.com/api/solve_again_weekplan',json=send_dict)
	else:
		response = requests.post(url='http://c5_autoplanner.planyourmeals.com/api/autoplan_week',json=send_dict)
	if response.status_code == requests.codes.ok:
		plan_dict = json.loads(response.text)
	else:
		print(response.text)
		return HttpResponse(status=500)
	plan_df = pd.DataFrame(plan_dict)
	if plan_df.empty:
		# Return message about possible problems
		min_req = {'nutrient':'default', 'req':10000}
		for key, val in requirements_dict.items():
			for key1, val1 in val.items():
				if val1[1]:
					diff = val1[1]
				else:
					diff = 100000
				if diff < min_req['req']:
					min_req['nut_abrev'] = key1
					min_req['req'] = diff
		message = 'The autoplanner was unable to find a meal plan from your menu. '+db_to_display_dict[min_req['nut_abrev']]+""" has a small window left. 
					Consider removing foods high in """+db_to_display_dict[min_req['nut_abrev']]+""" from your plan, adding """+db_to_display_dict[min_req['nut_abrev']]+"""-heavy foods to your menu
					 or relaxing the requirement. """
		if nth_solve>0:
			message = "The autoplanner has exhausted options for this scenario. Please use undo and redo to choose your plan or modify your menu for more options."
		return Response({'is_empty':True, 'message':message})
	# # Save to db
	date_list = []
	for menu in menus_dict_list:
		"""
		Make updates in Food Amount and Meal
		Make want to move this to be a method of Weekplan class. 
		"""
		plan_date_offset =  int(menu['day'].replace("day",""))-1
		plan_date = datetime.datetime.strptime(week_start_dt,"%Y-%m-%d") + datetime.timedelta(plan_date_offset)
		date_list.append(plan_date.date())
		for meal in menu['meals']:
			meal_type = meal['meal']
			loop_df = plan_df[(plan_df['day']==menu['day'])&(plan_df['meal']==meal_type)]
			# Get or create meal id
			plan_meal,_ = PlanMeal.objects.get_or_create(user_id = user_id, plan_date=plan_date, meal_type=meal_type)
			if not plan_meal.meal_id:
				meal = Meal.objects.create(user_id=user_id)
				meal_id = meal.id
				plan_meal.meal_id = meal_id
				plan_meal.save()
			else:
				meal_id = plan_meal.meal_id
			#if incl_replace:
			# Should instead *not* do this if a user wants to append to a snack
			Food_Amount.objects.filter(meal_id=meal_id).delete() # No longer clear all current foods from meal
			for idx, row in loop_df.iterrows():
				""" tuple:
				0 - index
				1 - unique_id
				2 - day
				3 - meal
				4 - dish_num
				5 - fd_type
				6 - amt
				7 - serving size val
				"""
				# Parse meal or food
				if(row['fd_type'])=='meal':
					# 
					all_foods = Food_Amount.objects.filter(meal_id =row['unique_id'])
					for food in all_foods:
						ss_val = float(Foods.objects.get(food_key=food.food_id).serving_size_val)
						Food_Amount.objects.create(food_id=food.food_id,
													amt=float(row['amt'])*float(food.amt),
													meal_id=meal_id,
													amount_divisor=ss_val) # not changing the meal, just its contents
						pref, pref_created= UserProbRejectMeal.objects.get_or_create(user_id=user_id,meal_id=row['unique_id'])
				else:
					Food_Amount.objects.create(food_id=row['unique_id'], 
												meal_id=meal_id,
												amt=row['amt']*1.0*row['serving_size_val'],
												amount_divisor=row['serving_size_val'])
					pref, pref_created= UserProbRejectFood.objects.get_or_create(user_id=user_id, food_id=row['unique_id'])
				if plan_date ==datetime.date.today():
					if pref_created:
						pref.last_view = datetime.date.today()
						pref.viewed = 1
					elif pref.last_view != datetime.date.today():
						pref.viewed+=1
						pref.last_view = datetime.date.today()
					pref.save()
	# Redux reducer to determine shape of returned data
	weekplan = WeekPlan()
	results = weekplan.get_weekplan(plan_date_tup=tuple(date_list),week_start_dt=datetime.datetime.strptime(week_start_dt,"%Y-%m-%d").date(), user_id=user_id)
	# add a meal id if it came from a meal. Not the current meal id, the original (meal_source_id)
	# Or meal_source_id could just be sent as a seperate list
	# Then when either is changed, the nth solve is triggered and it erases from list.
	results['is_empty'] = False
	return Response(results)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auto_adjust_week(request):
	"""
	Automatically adjusts amounts to fit reqs for any given number of days
	"""
	post_data = request.data['params'] # 'Params' from axios request
	day_incl_list = post_data['day_incl_list'] # [{'date':'10-10'2020','plannum':'day1':'meals':['Breakfast'], 'req_cols':['calories',' protein_g']}]
	#adjust_mult = post_data['adjust_mult']
	week_start_dt = post_data['week_start_dt']
	user_id = request.user.id
	success_dict={}
	date_list = []
	message = ''
	for day_dict in day_incl_list:
		req_cols = day_dict['req_cols']
		plannum = day_dict['plannum']
		meal_incl_list = day_dict['meals']
		plan_date = day_dict['date']
		date_list.append(day_dict['date'])
		adjust_mult = 0.5
		auto_adjuster = AmountAdjuster(req_cols, meal_incl_list, adjust_mult, user_id, plan_date, "../plm_env/lib/python3.6/site-packages/Cbc-2.9.8/bin/cbc", connection)
		return_df = auto_adjuster.solve_and_return_adjust()
		if sum(return_df['amt']) ==0:
			adjust_mult = 0.25
			auto_adjuster = AmountAdjuster(req_cols, meal_incl_list, adjust_mult, user_id, plan_date, "../plm_env/lib/python3.6/site-packages/Cbc-2.9.8/bin/cbc", connection)
			return_df = auto_adjuster.solve_and_return_adjust()

		if sum(return_df['amt']) !=0: 
			success_dict[plannum] = True
			for idx, row in return_df.iterrows():
				fd_am = Food_Amount.objects.get(meal_id=row['meal_id'], food_id=row['food_key'])
				fd_am.amt = row['amt'] * adjust_mult * row['amount_divisor']
				fd_am.save()
		else: 
			# Log some kind of notice
			message += str(plan_date)+ " could not meet requirements. Consider adding or removing foods. "
			success_dict[plannum] = False

	weekplan = WeekPlan()
	results = weekplan.get_weekplan(plan_date_tup=tuple(date_list),week_start_dt=datetime.datetime.strptime(week_start_dt,"%Y-%m-%d").date(), user_id=user_id)
	results['success_dict'] = success_dict
	results['is_empty'] = False
	return Response(results)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_food_alternative(request):
	"""
	Gets the current dictionary of requirements. 
	"""
	post_data = request.data['params'] # 'Params' from axios request
	reqs_dict = post_data['reqs_dict']
	food_key = post_data['food_key']
	menu_id = post_data['menu_id']
	plannum = post_data['plannum']
	meal_type = post_data['meal_type']
	user_id = request.user.id
	alt_qry = """
		SELECT
			f.food_key,
			f.food_description,
			f.brand,
			f.food_type_grp,
			f.image_url,
			f.serving_size_val,
			f.serving_size_unit,
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
			f.vit_c_mg,
			COALESCE(pr.max_servings, f.max_servings) as max_servings,
			pr.viewed,
			pr.removed,
			pr.dislike_ind,
			pr.last_view,
			alt.serving_sizes,
			cast(0 as int) as serving_size_idx,
			fi.*

		FROM core_foodpreferences fp

		JOIN food_foods f
			ON fp.food_id = f.food_key

		JOIN food_foodindex fi
			ON f.food_key = fi.food_id

		JOIN food_altservingsize alt
			ON f.food_key = alt.food_id

		LEFT JOIN core_userprobrejectfood pr
			ON f.food_key = pr.food_id
			AND pr.user_id = %(user_id)s

		WHERE fp.prefmenu_id= %(prefmenu_id)s and fp.food_id <> %(food_key)s
	"""
	qry_params = {'user_id':request.user.id,'user_id':user_id, 'food_key':food_key, 'prefmenu_id':menu_id}
	food_df = pd.read_sql(sql=alt_qry, params=qry_params, con=connection)
	food_df['last_view'] = food_df['last_view'].fillna(datetime.date(2018,1,1))
	food_df['last_view'] = pd.to_datetime(food_df['last_view'])
	food_df = food_df.fillna(0)
	prob_r = ((food_df['removed']+0.001)/(food_df['viewed']+0.002))*0.5  + food_df['dislike_ind']*2 + np.random.rand(len(food_df))*0.1 +1/(np.maximum([0.5]*len(food_df), food_df['viewed']-food_df['removed']))*0.3  + (1/(((datetime.date.today()-food_df['last_view'].dt.date).dt.days)+0.5))*0.2
	food_df = food_df.assign(prob_r = prob_r)
	alt_eng = AlternativesEngine(reqs_dict, food_df, food_key, user_id, plannum,meal_type, connection, "../plm_env/lib/python3.6/site-packages/Cbc-2.9.8/bin/cbc")
	alt_df = alt_eng.find_alternates(reqs_dict, food_df)
	if alt_df.empty:
		sim_df = alt_eng.find_similar(food_key, alt_df, reqs_dict, food_df, connection)
		sim_list = sim_df.to_dict('records')
	else:
		sim_list =[]
	alt_list = alt_df.to_dict('records')
	results={}
	results['alt_list'] = alt_list
	results['sim_list'] = sim_list
	results['alt_oth_list'] =[]
	return Response(results)
###
#	SHOPPING LIST
###
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_shopping_list_from_plan(request):
	"""
	Returns a shopping based on foods in plan between two dates
	"""
	post_data = request.data['params'] # 'Params' from axios request
	start_dt = post_data['start_date']
	end_dt =post_data['end_date']
	shopping_list_qry = '''
	SELECT
		  id,
		  food_description,
		  serving_size_unit,
		  sum(total_amount) as total_amount
	  FROM
	    (
	    SELECT
	      w.user_id as id,
	      f.food_description,
	      REPLACE(CAST(alt.serving_sizes->'ss_units'->am.serving_size_idx as varchar(30)),'"','') as serving_size_unit,
	      am.amt as total_amount
	    FROM plan_planmeal w
	    JOIN plan_meal m
	      ON w.meal_id = m.id
	    JOIN plan_food_amount am
	      ON (m.id = am.meal_id)
	    JOIN food_foods f
	      ON (am.food_id = f.food_key
	          AND f.food_type_grp in ('grocery','raw_ingredient'))
	    JOIN food_altservingsize alt
	      ON f.food_key = alt.food_id
	    WHERE w.user_id = %(user_id)s  AND w.plan_date >= %(start_dt)s AND w.plan_date <= %(end_dt)s
	    UNION ALL
	    SELECT 
	      w.user_id as id,
	      r.ingred_food_desc as food_description,
	      r.ingred_serving_size_unit as serving_size_unit,
	      r.ingred_amt as total_amount
	    FROM plan_planmeal w
	    JOIN plan_meal m
	      ON  w.meal_id = m.id
	    JOIN plan_food_amount am
	      ON (m.id = am.meal_id)
	    JOIN food_foods f
	      ON (am.food_id = f.food_key
	          AND f.food_type_grp IN ('recipe'))     
	    JOIN food_recipefood r 
	      ON (f.food_key = r.recipe_id)
	    WHERE w.user_id = %(user_id)s  AND w.plan_date >= %(start_dt)s AND w.plan_date <= %(end_dt)s
	    ) food_amounts
	    GROUP BY food_description, serving_size_unit, id
	ORDER BY food_description
	'''
	qry_params = {'user_id':request.user.id, 'start_dt':start_dt, 'end_dt':end_dt}
	list_df = pd.read_sql(sql=shopping_list_qry, params=qry_params, con=connection)
	list_df = list_df.fillna(0)
	list_list = list_df.to_dict('records')
	return Response({"list":list_list})