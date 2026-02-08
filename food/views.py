# django
from django.shortcuts import render
from django.core.serializers import serialize, deserialize
from django import core
from django.db import models
#from django.db.models import F
from django.db.models.expressions import connection
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
# rest framework
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
# 3rdr party
import pandas as pd
import json
import boto3
import os
from secrets import AK, SAK
# This app
from food.models import *
from core.models import *
from plan.models import *
# Create your views here.

#	***
# 	CONSTANTS
#	***
nutrients_const = ['calories','protein_g', 'fat_g','carb_g','saturated_fat_g','fiber_g','sugar_g','sodium_mg','cholesterol_mg','calcium_mg','iron_mg','vit_a_mcg','vit_c_mg']

###
#	Food Modal
###
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_food_modal(request):
	"""
	Returns all data needed for the modal view in a single response. Includes
		* food data and nutrients and default dishnum
		* tag info
		* menu / preferences info
		* food favorites info (stars) TODO - change model
		* amazonfresh link TODO - add model
		* comments and reviews TODO - add model
		* default serving size (prob_r) and user's dishnum
		* exclude this week
		* bad data flag -TODO - add model
	"""
	post_data = request.data['params'] # 'Params' from axios request
	food_key = post_data["food_key"]
	print(food_key)
	#food_dict = Foods.objects.get(food_key=food_key)
	food_dict = pd.read_sql(sql="select * from food_foods where food_key=%(food_key)s",params={'food_key':food_key},con=connection)\
			.to_dict('records')[0]
	taq_qry = """
		SELECT
			f.foodtag_id,
			t.name,
			f.added_by_id,
			case when f.added_by_id = %(user_id)s then 1 else 0 end as user_added_flg
		FROM food_taggedfoods f
		JOIN food_foodtags t
			ON f.foodtag_id = t.id
		WHERE  f.food_id = %(food_key)s
	"""
	tag_list = pd.read_sql(taq_qry,params={'food_key':food_key,'user_id':request.user.id},con=connection)\
		.to_dict('records')
	pref_qry="""
		SELECT 
			pm.*,
			fp.dish_num
		FROM core_prefmenu pm
		JOIN core_foodpreferences fp
			ON pm.id = fp.prefmenu_id
			AND fp.food_id = %(food_key)s
		WHERE pm.user_id = %(user_id)s AND default_flg=true
	"""
	pref_list = pd.read_sql(sql=pref_qry, params={'food_key':food_key, 'user_id':request.user.id},con=connection)\
		.to_dict('records')
	prob_r_qry = """
		SELECT
			f.viewed,
			f.removed,
			f.dislike_ind,
			f.last_view,
			COALESCE(f.max_servings,2) as max_servings,
			COALESCE(f.default_dish_num, fd.default_dish_num) as default_dish_num,
			f.user_total_uses,
			f.user_star_rating,
			g.global_star_rating,
			g.global_total_uses

		FROM core_GlobalProbRejectFood g
		JOIN food_foods fd
			ON g.food_id = fd.food_key
		LEFT JOIN core_UserProbRejectFood f
			ON g.food_id = f.food_id
			AND f.user_id = %(user_id)s

		WHERE g.food_id = %(food_key)s
	"""
	prob_r_dict = pd.read_sql(sql=prob_r_qry, params={'food_key':food_key, 'user_id':request.user.id},con=connection)\
			.to_dict('records')[0]
	# Exclusions Query
	excl_qry = """
		SELECT
			*
		FROM core_ExcludeFoods
			WHERE start_dt <= %(curr_dt)s AND food_id=%(food_key)s AND user_id=%(user_id)s
	"""
	# Not including initially
	# Recipe Query
	recipe_qry="""
		SELECT
			*
		FROM food_Recipes r
			JOIN food_RecipeSource s
				ON r.source_id = s.id
			JOIN food_RecipeFood rf
				ON r.food_id = rf.recipe_id
		WHERE r.food_id = %(food_key)s
	"""
	if food_dict['food_type_grp'] =='recipe':
		is_recipe=True
		recipe_list = pd.read_sql(sql=recipe_qry, params={'food_key':food_key}, con=connection)\
				.to_dict('records')
	else:
		is_recipe=False
		recipe_list =[]

	return Response({'food_dict':food_dict,'tag_list':tag_list, 
					'pref_list':pref_list,'prob_r_dict':prob_r_dict, 
					'is_recipe':is_recipe, 'recipe_list':recipe_list})

###
#	Food Tags
###
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_tag_autocomplete(request):
	post_data = request.data['params'] # 'Params' from axios request
	search_qry = post_data["search_qry"].lower()
	qry = """
		SELECT
			name,
			id,
			cast(1 as int) as user_added_flg

		FROM food_FoodTags
		WHERE name LIKE %(search_qry_like)s
	"""
	search_results = pd.read_sql(sql=qry,params={"search_qry_like":search_qry+"%"},con=connection) # one-sided "like" = "starts with"
	tag_search_list = search_results.to_dict("records")
	return Response({"tag_search_list":tag_search_list})

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def update_tags_from_list(request):
# 	post_data = request.data['params']
# 	food_key = post_data["food_key"]
# 	tag_list = post_data["tag_list"] 
# 	tag_list.reverse()# reverse the list so that in case of duplicates the first person who added gets credit?
# 	TaggedFoods.objects.filter(food_id=food_key).delete() # Nooo
# 	for tag_obj in tag_list:
# 		# Tag_Name is object with "name", "foodtag_id", and "added_by_id"
# 		food_tag,_ = FoodTags.objects.get_or_create(name=tag_obj["name"])
# 		if tag_obj["added_by_id"] ==0:
# 			user_id = request.user.id
# 		else:
# 			user_id = tag_obj["added_by_id"]
# 		tagged_food,_ = TaggedFoods.objects.get_or_create(food_id=food_key,user_id=user_id, foodtag_id=food_tag.id)
# 	return Response({"status":"success"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_food_tag(request):	
	post_data = request.data['params']
	food_key = post_data["food_key"]
	tag_name = post_data["tag_name"]
	food_tag,_ = FoodTags.objects.get_or_create(name=tag_name)
	if not TaggedFoods.objects.filter(foodtag_id=food_tag.id, food_id=food_key).exists():
		print(str(food_tag.id))
		TaggedFoods.objects.create(foodtag_id=food_tag.id, food_id=food_key, added_by_id=request.user.id)
	return Response({"status":"success"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_food_tag(request):	
	post_data = request.data['params']
	food_key = post_data["food_key"]
	tag_name = post_data["tag_name"]
	food_tag,_ = FoodTags.objects.get_or_create(name=tag_name)
	TaggedFoods.objects.filter(foodtag_id=food_tag.id, food_id=food_key, added_by_id=request.user.id).delete()
	return Response({"status":"success"})

###
#	Add Recipe
###

def save_recipe_image(image_file, use_default, food_key):
	"""
	This is a giant pain, but it seems like the image uploads fine, but the browser has to wait to clear its cache to see it
	"""
	s3_client = boto3.client('s3',
		aws_access_key_id=AK,
		aws_secret_access_key=SAK,
	)
	# statObj = os.stat(image_file)
	# print(statObj.st_size)
	# s3_resource = boto3.resource('s3',
	# 	     aws_access_key_id=AK,
	# 	     aws_secret_access_key=SAK,
	# 	     region_name='us-east-1',
	# )
	# bucket = s3_resource.Bucket("planyourmealsmedia")
	try:
		if use_default:

			result = s3_client.upload_file("default_thumbnail.png", "planyourmealsmedia","food/"+str(food_key)+"/thumbnail.png")
		else:
			result = s3_client.put_object(Bucket="planyourmealsmedia",Body=image_file,Key="food/"+str(food_key)+"/thumbnail.png")
			#s3_resource.Object("planyourmealsmedia", "food/"+str(food_key)+"/thumbnail.png").put(Body=image_file)
			#result=bucket.put_object(Body=image_file,Key="food/"+str(food_key)+"/thumbnail.png")
	except:
		pass

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_recipe(request):
	post_data = request.data
	ingredients_list = json.loads(post_data['ingredients_list'])
	ingredients_list = [json.loads(l) for l in ingredients_list]
	servings = post_data['yield']
	try:
		image_file = request.FILES['recipe_image'].read()
		use_default=False
	except:
		image_file=''
		use_default=True
	name = post_data['recipe_name'].lower()
	desc = post_data['recipe_description'].lower()
	instructions_list = json.loads(post_data["instructions_list"])
	default_dish_num = post_data["default_dish_num"]
	max_servings = post_data["max_servings"]
	ct_hrs = post_data["cook_time_hours"]
	ct_mins = post_data["cook_time_minutes"]
	# Creating Dictionary To Get Nutrient Totals
	nut_dict = dict(zip(nutrients_const, [0]*len(nutrients_const) ))
	for ingred_dict in ingredients_list:
		ingred = Foods.objects.get(food_key=ingred_dict["food_key"])
		ingred_ss = AltServingSize.objects.get(food_id=ingred_dict["food_key"])
		fd_amt_adj = round(float(ingred_dict["amt"])/float(ingred_ss.serving_sizes['ss_amts'][ingred_dict["serving_size_idx"]]), 4) # amount times serving size val
		for nut in nutrients_const:
			if getattr(ingred, nut) == None:
				pass
			else:
				nut_dict[nut] = nut_dict[nut] + round((float(getattr(ingred, nut))*float(ingred_dict["amt"]))/float(servings),2)

	food_key = Foods.objects.all().aggregate(models.Max('food_key'))['food_key__max'] + 1 # food key 
	# Create Food Object
	new_food = Foods.objects.create(
			food_key = food_key,
            food_description=name,
            brand='recipe', 
            food_type_grp='recipe',
            source='user_entered_recipe',
            serving_size_raw='1 serving',
            serving_size_val=1.0,
            serving_size_unit='serving',
            calories=nut_dict['calories'],
            protein_g=nut_dict['protein_g'],
            fat_g=nut_dict['fat_g'],
            carb_g=nut_dict['carb_g'],
            fiber_g=nut_dict['fiber_g'],
            sugar_g=nut_dict['sugar_g'],
            sodium_mg=nut_dict['sodium_mg'],
            cholesterol_mg=nut_dict['cholesterol_mg'],
            saturated_fat_g=nut_dict['saturated_fat_g'],
            calcium_mg=nut_dict['calcium_mg'],
            iron_mg=nut_dict['iron_mg'],
            vit_a_mcg=nut_dict['vit_a_mcg'],
            vit_c_mg=nut_dict['vit_c_mg'],
            default_dish_num=default_dish_num,
            max_servings=max_servings,
            image_url = 'https://planyourmealsmedia.s3.amazonaws.com/food/'+str(food_key)+"/thumbnail.png"		
		)
	save_recipe_image(image_file, use_default, food_key)
	# Create Food Index Object
	new_food_index = FoodIndex.objects.create(
		food_id=new_food.food_key,
        pro_index=round(nut_dict['protein_g']/nut_dict['calories'],4),
        fat_index=round(nut_dict['fat_g']/nut_dict['calories'],4),
        car_index=round(nut_dict['carb_g']/nut_dict['calories'],4),
        fib_index=round(nut_dict['fiber_g']/nut_dict['calories'],4),
        clc_index=round(nut_dict['calcium_mg']/nut_dict['calories'],4),
        irn_index=round(nut_dict['iron_mg']/nut_dict['calories'],4),
        vta_index=round(nut_dict['vit_a_mcg']/nut_dict['calories'],4),
        vtc_index=round(nut_dict['vit_c_mg']/nut_dict['calories'],4),
        sug_index=round(nut_dict['sugar_g']/nut_dict['calories'],4),
        stf_index=round(nut_dict['saturated_fat_g']/nut_dict['calories'],4),
        sod_index=round(nut_dict['sodium_mg']/nut_dict['calories'],4),
        cho_index=round(nut_dict['cholesterol_mg']/nut_dict['calories'],4)
		)
	# Create Alt Serving Sizes Object
	alt_ss = AltServingSize.objects.create(food_id=new_food.food_key, serving_sizes={'ss_amts':[1], 'ss_units':['serving']})
	# Create Recipe Source Object
	src, __ = RecipeSource.objects.get_or_create(source_name=request.user.id, is_user=True)
	# Create Recipes Object
	new_recipe = Recipes.objects.create(food_id=new_food.food_key, 
			description=desc,
			recipe_yield=int(servings), 
			added_by_id=request.user.id,
			source_id=src.id,
			instructions = instructions_list,
			num_ingred=len(ingredients_list))
	if ct_hrs or ct_mins:
		if not(ct_hrs):
			ct_hrs = 0
		if not(ct_mins):
			ct_mins = 0
		new_recipe.cook_time={"hrs":int(ct_hrs),"mins":int(ct_mins)}
	new_recipe.save()
    # Create Recipe Foods Object
	for ingred_food in ingredients_list:
		new_rec_food = RecipeFood.objects.create(recipe_id=new_recipe.food_id,
			ingred_food_desc=ingred_food["food_description"], 
			ingred_food_id=ingred_food["food_key"],
			ingred_amt=ingred_food["amt"],
			ingred_serving_size_unit=ingred_food["serving_sizes"]["ss_units"][ingred_food["serving_size_idx"]])
	# Create globalprobr object
	GlobalProbRejectFood.objects.create(food_id=new_food.food_key)
	# Create userprobr object
	UserProbRejectFood.objects.create(food_id=new_food.food_key, user=request.user, max_servings=max_servings,default_dish_num=default_dish_num)
	# Upload food image
	return Response({"food_key":new_food.food_key})

###
#	Edit Recipe
###
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_recipes_for_edit(request):
	"""
	Returns recipes to edit or clone
	"""
	post_data = request.data['params'] # 'Params' from axios request
	search_qry = post_data['search_qry'].lower()
	food_type_grp = post_data['food_type_grp']
	qry = """
		SELECT
			f.*,
			s.serving_sizes,
			CASE WHEN f.food_description = %(search_qry)s THEN 0 ELSE 1 END AS order,
			f.serving_size_val as amt,
			0 as serving_size_idx
		FROM food_foods f
			JOIN food_altservingsize s
				ON f.food_key = s.food_id
			JOIN food_recipes r
				ON f.food_key = r.food_id
				AND r.added_by_id =  %(user_id)s
		WHERE f.food_description LIKE %(search_qry_like)s
			AND f.food_type_grp in %(food_type_grp)s
		ORDER BY CASE WHEN f.food_description = %(search_qry)s THEN 0 ELSE 1 END
		LIMIT 100
	"""
	qry_params = {"search_qry":search_qry, "search_qry_like":search_qry+"%", "food_type_grp":tuple(food_type_grp), 'user_id':request.user.id }
	df = pd.read_sql(sql=qry,params=qry_params, con=connection)
	df = df.fillna(0)
	df_rec = df.to_dict('records') # records is shape [{col->val}, {col->val}]
	#df_rec = df.to_dict('index') # index is shape {idx:{col->val},idx:{col->val}}
	return Response({'search_results_by_id':df_rec})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_recipe_for_edit(request):
	"""
	Returns all editable recipe details for a given food key
	"""
	post_data = request.data['params'] # 'Params' from axios request
	food_key = post_data["food_key"]
	recipe_obj_qry="""
		SELECT
			f.*,
			r.*
		FROM food_foods f
			JOIN food_recipes r
				ON f.food_key = r.food_id
		WHERE f.food_key = %(food_key)s
	"""
	qry_params = {'food_key':food_key}
	recipe_df = pd.read_sql(sql=recipe_obj_qry,params=qry_params, con=connection)
	# Wrong - need to left join on food foods. Eff.
	ingred_qry = """
		SELECT
			f.*,
			rf.*,
			a.serving_sizes
		FROM food_foods f
			JOIN food_RecipeFood rf
				ON f.food_key = rf.ingred_food_id
				AND rf.recipe_id = %(food_key)s
			JOIN food_altservingsize a
				on f.food_key = a.food_id
	"""
	ingred_df = pd.read_sql(sql=ingred_qry, params=qry_params, con=connection)
	recipe_df = recipe_df.fillna(0)
	ingred_df = ingred_df.fillna(0)
	ingred_df = ingred_df.rename(mapper={'ingred_amt':'amt'}, axis=1)
	def return_ss_idx(serving_size_units, unit):
		return serving_size_units.index(unit)
	#ingred_df = ingred_df.assign(serving_size_idx=ingred_df.apply(lambda x:return_ss_idx(x['serving_sizes']['ss_units'], x['ingred_serving_size_unit'])), axis=1)
	#ingred_df = ingred_df.assign(serving_size_idx=ingred_df.apply(lambda x:print(x)), axis=0)
	ingred_ss_idx_list = []
	for index, row in ingred_df.iterrows():
		ingred_ss_idx_list.append(return_ss_idx(row['serving_sizes']['ss_units'],row['ingred_serving_size_unit']))
	ingred_df = ingred_df.assign(serving_size_idx=ingred_ss_idx_list)
	recipe_dict = recipe_df.to_dict('records')[0]
	ingred_list = ingred_df.to_dict('records')
	return Response({'recipe_dict':recipe_dict,'ingred_list':ingred_list})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_recipe(request):
	"""
	Edit all entries for a given recipe
	"""
	post_data = request.data
	#print(post_data)
	# add image upload here
	food_key = post_data['food_key']
	try:
		image_file = request.FILES['recipe_image'].read()
		save_recipe_image(image_file, False, food_key)
	except:
		pass # don't update image
	instructions_list = json.loads(post_data["instructions_list"])
	ingredients_list = json.loads(post_data['ingredients_list'])
	ingredients_list = [json.loads(l) for l in ingredients_list]
	servings = post_data['yield']
	name = post_data['recipe_name'].lower()
	desc = post_data['recipe_description'].lower()
	default_dish_num = post_data["default_dish_num"]
	max_servings = post_data["max_servings"]
	try:
		ct_hrs = post_data["cook_time_hours"]
	except:
		ct_hrs = None
	try:
		ct_mins = post_data["cook_time_minutes"]
	except:
		ct_mins= None
	# Creating Dictionary To Get Nutrient Totals
	nut_dict = dict(zip(nutrients_const, [0]*len(nutrients_const)))
	for ingred_dict in ingredients_list:
		ingred = Foods.objects.get(food_key=ingred_dict["food_key"])
		ingred_ss = AltServingSize.objects.get(food_id=ingred_dict["food_key"])
		fd_amt_adj = round(float(ingred_dict["amt"])/float(ingred_ss.serving_sizes['ss_amts'][ingred_dict["serving_size_idx"]]), 4) # amount times serving size val
		for nut in nutrients_const:
			if getattr(ingred, nut) == None:
				pass
			else:
				nut_dict[nut] = nut_dict[nut] + round((float(getattr(ingred, nut))*float(ingred_dict["amt"]))/float(servings),2)

	#mx_key = Foods.objects.all().aggregate(models.Max('food_key'))['food_key__max'] # food key 
	# Get Food Object and save new features
	food = Foods.objects.get(food_key = food_key)
	food.food_description=name
	food.brand='recipe' 
	food.food_type_grp='recipe'
	food.source='user_entered_recipe'
	food.serving_size_raw='1 serving'
	food.serving_size_val=1.0
	food.serving_size_unit='serving'
	food.image_url = 'https://planyourmealsmedia.s3.amazonaws.com/food/'+str(food_key)+"/thumbnail.png"
	food.calories=nut_dict['calories']
	food.protein_g=nut_dict['protein_g']
	food.fat_g=nut_dict['fat_g']
	food.carb_g=nut_dict['carb_g']
	food.fiber_g=nut_dict['fiber_g']
	food.sugar_g=nut_dict['sugar_g']
	food.sodium_mg=nut_dict['sodium_mg']
	food.cholesterol_mg=nut_dict['cholesterol_mg']
	food.saturated_fat_g=nut_dict['saturated_fat_g']
	food.calcium_mg=nut_dict['calcium_mg']
	food.iron_mg=nut_dict['iron_mg']
	food.vit_a_mcg=nut_dict['vit_a_mcg']
	food.vit_c_mg=nut_dict['vit_c_mg']
	food.default_dish_num=default_dish_num
	food.max_servings=max_servings			
	food.save()
	# Update Food Index Object
	food_index = FoodIndex.objects.get(food_id=food_key)
	food_index.pro_index=round(nut_dict['protein_g']/nut_dict['calories'],4)
	food_index.fat_index=round(nut_dict['fat_g']/nut_dict['calories'],4)
	food_index.car_index=round(nut_dict['carb_g']/nut_dict['calories'],4)
	food_index.fib_index=round(nut_dict['fiber_g']/nut_dict['calories'],4)
	food_index.clc_index=round(nut_dict['calcium_mg']/nut_dict['calories'],4)
	food_index.irn_index=round(nut_dict['iron_mg']/nut_dict['calories'],4)
	food_index.vta_index=round(nut_dict['vit_a_mcg']/nut_dict['calories'],4)
	food_index.vtc_index=round(nut_dict['vit_c_mg']/nut_dict['calories'],4)
	food_index.sug_index=round(nut_dict['sugar_g']/nut_dict['calories'],4)
	food_index.stf_index=round(nut_dict['saturated_fat_g']/nut_dict['calories'],4)
	food_index.sod_index=round(nut_dict['sodium_mg']/nut_dict['calories'],4)
	food_index.cho_index=round(nut_dict['cholesterol_mg']/nut_dict['calories'],4)
	food_index.save()
	# Don't update Alt Serving Sizes Object for now bc no fields
	# Don't update Recipe Source Object for now bc no fields
	# Update Recipes Object
	recipe = Recipes.objects.get(food_id=food_key)
	recipe.description=desc
	recipe.recipe_yield=int(servings) 
	recipe.instructions = instructions_list
	recipe.num_ingred=len(ingredients_list)
	if ct_hrs or ct_mins:
		if not(ct_hrs):
			ct_hrs = 0
		if not(ct_mins):
			ct_mins = 0
	recipe.cook_time={"hrs":int(ct_hrs),"mins":int(ct_mins)}
	recipe.save()
	# Delete Old and Create New Foods Objects
	RecipeFood.objects.filter(recipe_id=food_key).delete()
	for ingred_food in ingredients_list:
		new_rec_food = RecipeFood.objects.create(recipe_id=food_key,
    		ingred_food_desc=ingred_food["food_description"], 
			ingred_food_id=ingred_food["food_key"],
			ingred_amt=ingred_food["amt"],
			ingred_serving_size_unit=ingred_food["serving_sizes"]["ss_units"][ingred_food["serving_size_idx"]])
	return Response({"food_key":food_key})

