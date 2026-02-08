# django
from django.shortcuts import render
from django.db.models.expressions import connection
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.mail import send_mail
# from django.core import serializers
from django.http import HttpResponseRedirect, JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
# Other Python
import pandas as pd
import datetime
import boto3
import os
from secrets import AK, SAK
# This app
from django.contrib.auth.models import User
from core.serializers import *
from plan.views import WeekPlan
from core.models import *
from plan.models import EmailLeads
from .forms import BlogForm
from secrets import STRIPE_API_KEY
# third party
import stripe
from rest_auth.registration.views import SocialConnectView, SocialLoginView
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
# google
from .googleviews import GoogleOAuth2AdapterIdToken # import custom adapter
# logs
# WHY NOT USING ? Celery interferes with these base loggers. 
# TODO - Setup all loggers to share logger with celery
# import logging
# logging.basicConfig(filename='../logs/core.log',level=logging.INFO)
# app
# Create your views here.

#   ***
#   CONSTANTS
#   ***
nut_abrev_list= ['cal','pro','fat','car','fib','clc','irn','vta', 'vtc','sug', 'stf','sod','cho', 'nca', 'nsu']

menu_qry="""
        SELECT
            f.food_key  as unique_id,
            cast('food' as varchar(12)) as item_type,
            m.meal_type,
            m.dish_num,
            f.food_description as name

        FROM core_foodpreferences m

        JOIN core_prefmenu pm
            ON m.prefmenu_id = pm.id
            AND pm.user_id = %(user_id)s

        JOIN food_foods f 
            ON m.food_id = f.food_key 

        WHERE  pm.user_id = %(user_id)s AND pm.id IN %(prefmenu_id_list)s
        UNION
        SELECT
            m.meal_id  as unique_id,
            cast('meal' as varchar(12)) as item_type,
            m.meal_type,
            m.dish_num,
            p.mealname as name

        FROM core_mealpreferences m
        
        JOIN core_prefmenu pm
            ON m.prefmenu_id = pm.id
            AND pm.user_id = %(user_id)s

        JOIN plan_meal p
            ON m.meal_id = p.id

        WHERE  pm.user_id = %(user_id)s AND pm.id IN %(prefmenu_id_list)s
        UNION
        SELECT
            m.tag_id as unique_id,
            cast('tag' as varchar(12)) as item_type,
            m.meal_type,
            m.dish_num,
            t.name

        FROM core_foodtagpreferences m
        
        JOIN core_prefmenu pm
            ON m.prefmenu_id = pm.id
            AND pm.user_id = %(user_id)s

        JOIN food_foodtags t
            ON m.tag_id = t.id

        WHERE  pm.user_id = %(user_id)s AND pm.id IN %(prefmenu_id_list)s
        UNION
        SELECT
            m.restaurant_id  as unique_id,
            cast('restaurant' as varchar(12)) as item_type,
            m.meal_type,
            m.dish_num,
            r.restaurant as name

        FROM core_restaurantpreferences m
        
        JOIN core_prefmenu pm
            ON m.prefmenu_id = pm.id
            AND pm.user_id = %(user_id)s

        JOIN food_restaurants r
            ON m.restaurant_id = r.id

        WHERE  pm.user_id = %(user_id)s AND pm.id IN %(prefmenu_id_list)s
    """


#   ***
#   NON-VIEW FUNCTIONS
#   ***
def clone_menu(user_id, cloner_id, delete_existing):
    """
        user_id: user_id of menu to clone to
        cloner_id: id of PublicMenu object to clone from
        delete_existing: Boolean object to say whether to remove existing Preference objects
    """
    cloner_menu = PublicMenu.objects.get(id=cloner_id)
    user_menu, created = UserMenu.objects.get_or_create(user_id=user_id)
    # This step makes it PARAMOUNT that default_flg exists only once for a user, and are always referenced by UserMenu
    if created:
        user_br = PrefMenu.objects.create(user=user_id,create_user=user_id,default_flg=True, meal_type='Breakfast', menu_name="Default Breakfast")
        user_lu = PrefMenu.objects.create(user=user_id,create_user=user_id,default_flg=True, meal_type='Lunch',menu_name="Default Lunch")
        user_di = PrefMenu.objects.create(user=user_id,create_user=user_id,default_flg=True, meal_type='Dinner',menu_name="Default Dinner")
        user_sn = PrefMenu.objects.create(user=user_id,create_user=user_id,default_flg=True, meal_type='Snack',menu_name="Default Snack")
    else:
        # Shouldn't have to check for a null mealtype_prefmenu_id, but is a good id
        user_br = PrefMenu.objects.get(id=user_menu.breakfast_prefmenu_id)
        user_lu = PrefMenu.objects.get(id=user_menu.lunch_prefmenu_id)
        user_di = PrefMenu.objects.get(id=user_menu.dinner_prefmenu_id)
        user_sn = PrefMenu.objects.get(id=user_menu.snack_prefmenu_id)

    # This is double-check if UserMenu is referencing the correct PrefMenu objects
    meal_type_menu_dict = {'Breakfast': user_br.id, 'Lunch':user_lu.id, 'Dinner':user_di.id, 'Snack':user_sn.id}
    pref_menu_id_list = [cloner_obj.breakfast_prefmenu_id,cloner_obj.lunch_prefmenu_id,cloner_obj.dinner_prefmenu_id,cloner_obj.snack_prefmenu_id]            
    # Delete If Requested
    if delete_existing:
        FoodPreferences.objects.filter(prefmenu_id__in=[user_br.id, user_lu.id, user_di.id, user_sn.id]).delete()
    # Copy Over 
    fd_prefs = FoodPreferences.objects.filter(prefmenu_id__in=pref_menu_id_list) # Default Breakfast
    for fd in fd_prefs:
        FoodPreferences.objects.create(meal_type=fd.meal_type, prefmenu_id=meal_type_menu_dict[fd.meal_type],dish_num=fd.dish_num,food_id=fd.food_id )
    ml_prefs = MealPreferences.objects.filter(prefmenu_id__in=pref_menu_id_list)
    for ml in ml_prefs:
        MealPreferences.objects.create(meal_type=ml.meal_type, prefmenu_id=meal_type_menu_dict[ml.meal_type],dish_num=ml.dish_num,meal_id=ml.meal_id)
    rest_prefs = RestaurantPreferences.objects.filter(prefmenu_id__in=pref_menu_id_list)
    for rest in rest_prefs:
        RestaurantPreferences.objects.create(meal_type=rest.meal_type, prefmenu_id=meal_type_menu_dict[rest.meal_type],dish_num=rest.dish_num,restaurant_id=rest.restaurant_id)
    fd_tg_prefs = FoodTagPreferences.objects.filter(prefmenu_id__in=pref_menu_id_list)
    for fd_tg in fd_tg_prefs:
        FoodTagPreferences.objects.create(meal_type=fd_tg.meal_type, prefmenu_id=meal_type_menu_dict[fd_tg.meal_type],dish_num=fd_tg.dish_num,tag_id=fd_tg.tag_id)
    ml_tg_prefs = MealTagPreferences.objects.filter(prefmenu_id__in=pref_menu_id_list)
    for ml_tg in ml_tg_prefs:
        MealTagPreferences.objects.create(meal_type=ml_tg.meal_type, prefmenu_id=meal_type_menu_dict[ml_tg.meal_type],dish_num=ml_tg.dish_num,tag_id=ml_tg.tag_id)

    return 'success'

def query_menus(params):
    """
    Querys menus based on Params parameter - which includes a list of prefmenu ids, and a user id
    """
    meals = ['Breakfast', 'Lunch', 'Dinner', 'Snack']
    dishes = ['whole_meals', 'main_courses', 'sides']
    menu_lists_df = pd.read_sql(sql=menu_qry, params=params, con=connection)
    
    if not menu_lists_df.empty:
        menu_lists_df['dish_num'] = menu_lists_df['dish_num'].apply(lambda x: x.lower().replace(' ','_'))
        menu_lists_df  = menu_lists_df.groupby(['meal_type','dish_num'])\
                                        .apply(lambda x: x.to_dict('records'))\
                                        .to_frame('items_list')
        menu_dict = menu_lists_df.groupby(level=0)\
                    .apply(lambda x: x.xs(x.name).to_dict('index')).to_dict()
    else:
        menu_dict = {}
    # Ensure no missing meals or dishes
    for meal in meals:
        if meal not in menu_dict:
            menu_dict[meal] = {}
        if meal != 'Snack':
            for dish in dishes:
                if dish not in menu_dict[meal]:
                    menu_dict[meal][dish] = {'items_list':[]}
        else:
            if 'snacks' not in menu_dict['Snack']:
                menu_dict['Snack']['snacks'] =  {'items_list':[]}

    return menu_dict

#   ***
#   STARTUP
#   ***
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_user_reqs_and_menus(request):
    """
    Returns initial nutrient requirements, default plan menus, and nutrients to include in plan
    Called on plan re-render
    All these queries should use async
    """
    post_data = request.data['params']
    date_list = post_data["date_list"]
    week_start_dt=  post_data["week_start_dt"]
    user_id  = request.user.id
    #start_date = 
    # Default Menu Ids
    default_menus_qry ="""
        SELECT
            pm.id, 
            menu_name as name, 
            meal_type, 
            'menu' as type,
            um.id as usermenu_id
        FROM core_prefmenu pm
        JOIN core_usermenu um
            ON um.user_id = pm.user_id
            AND (  pm.id = um.breakfast_prefmenu_id 
                OR pm.id = um.lunch_prefmenu_id 
                OR pm.id = um.dinner_prefmenu_id 
                OR pm.id = um.snack_prefmenu_id )
        WHERE pm.user_id=%(user)s
    """
    #default_menus_df = pd.read_sql(sql="select id, menu_name as name, meal_type, 'menu' as type from core_prefmenu where user_id=%(user)s and default_flg=true",params={'user':request.user.id}, con=connection)
    default_menus_df = pd.read_sql(sql=default_menus_qry,params={'user':request.user.id}, con=connection)
    default_menus_df.index = default_menus_df['meal_type']
    default_menus =  default_menus_df.to_dict('index')
    # Menu Items
    menu_params ={'user_id':request.user.id, 'prefmenu_id_list':(default_menus['Breakfast']['id'],default_menus['Lunch']['id'],default_menus['Dinner']['id'],default_menus['Snack']['id'])}
    menu_dict = query_menus(menu_params)
    # Default User Nutrient settings
    prof_qry ="""
        SELECT
            p.*,
            a.email,
            ua.status
        FROM core_profile p
        JOIN auth_user a 
            ON p.user_id = a.id
        JOIN core_useraccount ua
            ON p.user_id = ua.user_id
        WHERE p.user_id=%(user)s
    """
    user_profile = pd.read_sql(sql=prof_qry, params={'user':request.user.id}, con=connection)
    autoplan_nutrients = user_profile[['cal','pro','fat','car','stf', 'fib', 'sug', 'sod', 'clc', 'cho', 'irn', 'vta', 'vtc']].to_dict('records')
    requirements_dict = user_profile[[
                            'cal_ub','cal_lb',
                            'pro_ub', 'pro_lb',
                            'car_ub', 'car_lb',
                            'fat_ub', 'fat_lb',
                            'stf_ub', 'stf_lb',
                            'fib_ub', 'fib_lb',
                            'sug_ub', 'sug_lb',
                            'sod_ub', 'sod_lb',
                            'cho_ub', 'cho_lb',
                            'clc_ub', 'clc_lb',
                            'irn_ub', 'irn_lb',
                            'vta_ub', 'vta_lb',
                            'vtc_ub', 'vtc_lb']].to_dict('records')
    user_stats = user_profile[['weight',
                                'weight_unit', 
                                'height_feet',
                                'height_inches', 
                                'age', 
                                'sex', 
                                'activity', 
                                'cal_adj',
                                'pro_perc', 
                                'fat_perc',
                                'car_perc',
                                'first_session',
                                'email',
                                'status']].to_dict('records')
    weekplan = WeekPlan()
    results = weekplan.get_weekplan(plan_date_tup=tuple(date_list),week_start_dt=datetime.datetime.strptime(week_start_dt,"%Y-%m-%d").date(), user_id=user_id)
    # TODO - get user email and account status
    return Response({'autoplan_nutrients':autoplan_nutrients[0],'requirements_dict':requirements_dict[0],
                'default_menus':default_menus, 'weekplan':results,'user_stats':user_stats[0],'menu_dict':{'menus':menu_dict}})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_user_nut_reqs(request):
    """
    Returns initial nutrient requirements
    Called on nutrients page re-render
    """ 
    post_data = request.data['params']
    user_profile = pd.read_sql(sql="select * from core_profile where user_id=%(user)s", params={'user':request.user.id}, con=connection)
    autoplan_nutrients = user_profile[['cal','pro','fat','car','stf', 'fib', 'sug', 'sod', 'clc', 'cho', 'irn', 'vta', 'vtc']].to_dict('records')
    requirements_dict = user_profile[[
                            'cal_ub','cal_lb',
                            'pro_ub', 'pro_lb',
                            'car_ub', 'car_lb',
                            'fat_ub', 'fat_lb',
                            'stf_ub', 'stf_lb',
                            'fib_ub', 'fib_lb',
                            'sug_ub', 'sug_lb',
                            'sod_ub', 'sod_lb',
                            'cho_ub', 'cho_lb',
                            'clc_ub', 'clc_lb',
                            'irn_ub', 'irn_lb',
                            'vta_ub', 'vta_lb',
                            'vtc_ub', 'vtc_lb']].to_dict('records')
    user_stats = user_profile[['weight','weight_unit', 'height_feet','height_inches', 'age', 'sex', 'activity', 'cal_adj','pro_perc', 'fat_perc','car_perc']].to_dict('records')
    return Response({'user_stats':user_stats[0],'requirements_dict':requirements_dict[0]})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def return_acct_status(request):
    """
    Is meant to validate token and return account status is valid
    """
    status = UserAccount.objects.get(user_id=request.user.id).status
    return Response({'user_status':status})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def close_onboarding(request):
    """
    Is no longer a first-time user. Do not show onboarding modal going forward
    """
    profile = Profile.objects.get(user_id=request.user.id)
    profile.first_session=False
    profile.save()
    return Response({"status":"success"})
#   ***
#   AUTH
#   ***
class FacebookConnect(SocialConnectView):
    adapter_class = FacebookOAuth2Adapter

class FacebookLogin(SocialLoginView):
    # setup for access_token config
    adapter_class = FacebookOAuth2Adapter
    client_class = OAuth2Client

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2AdapterIdToken
    client_class = OAuth2Client

class ConfirmEmailView(APIView):
    """
    Overriding allauth's default ConfirmEmailView
    """
    permission_classes = [AllowAny]
    def get(self, *args, **kwargs):
        self.object = confirmation = self.get_object()
        confirmation.confirm(self.request)
        return HttpResponseRedirect('https://planyourmeals.com/')

    def get_object(self, queryset=None):
        key = self.kwargs['key']
        email_confirmation = EmailConfirmationHMAC.from_key(key)
        if not email_confirmation:
            if queryset is None:
                queryset=self.get_queryset()
            try:
                email_confirmation = queryset.get(key=key.lower())
            except EmailConfirmation.DoesNotExist:
                return HttpResponseRedirect('/bad_email_conf/')
        return email_confirmation

    def get_queryset(self):
        qs = EmailConfirmation.objects.all_valid()
        qs = qs.select_related("email_address__user")
        return qs

# NOT an API!
def bad_email_conf(request):
    """
    Displays a page for bad email
    """
    return render(request, 'bad_email.html')

def password_reset_confirm(request):
    pass

#   ***
#   MENUS
#   ***
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def autocomplete_menus(request):
    """
    Takes in search queries from autocomplete.
    Could run these all seperately using async as well. 
    """
    search_qry = request.data["params"]["search_query"].lower()
    meal_type = request.data["params"]["meal_type"]
    qry = """
        SELECT 
            id,
            'menu' as type,
            menu_name as name
        FROM core_prefmenu
        WHERE lower(menu_name) like %(search_like)s and meal_type = %(meal_type)s and user_id=%(user_id)s
        UNION
        SELECT
            id,
            'tag' as type,
            name
        FROM food_foodtags
        WHERE lower(name) like %(search_like)s
        UNION
        SELECT
            id, 
            'restaurant' as type,
            restaurant as name
        FROM food_restaurants
        WHERE restaurant like %(search_like)s
    """
    search_results = pd.read_sql(sql=qry,params={"search_like":"%"+search_qry+"%", "meal_type":meal_type, "user_id":request.user.id},con=connection)
    search_results = search_results.sort_values(by='type')
    search_results_dict = search_results.to_dict("records")
    return Response({"search_results":search_results_dict})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_menu_items(request):
    post_data = request.data["params"]
    search_qry = post_data["search_qry"].lower()
    item_type = post_data["item_type"] # should stay exclusive, i.e. not a list or 'all'

    if item_type=='meal':
        qry = """
            SELECT
                id as unique_id,
                'meal' as item_type,
                mealname as name,
                case when mealname = %(search_qry)s then 0 else 1 end as order
            FROM plan_meal
            WHERE mealname like %(search_qry_like)s
            ORDER BY case when mealname = %(search_qry)s then 0 else 1 end
            LIMIT 100
        """
        results =  pd.read_sql(sql=qry, params={'search_qry':search_qry, 'search_qry_like':search_qry+"%"}, con=connection)
    elif item_type=='tag':
        qry = """
            SELECT
                id as unique_id,
                'tag' as item_type,
                name,
                case when name = %(search_qry)s then 0 else 1 end as order
            FROM food_FoodTags
            WHERE name like %(search_qry_like)s
            ORDER BY case when name = %(search_qry)s then 0 else 1 end
            LIMIT 100
        """
        results =  pd.read_sql(sql=qry, params={'search_qry':search_qry, 'search_qry_like':search_qry+"%"}, con=connection)
    elif item_type=='brand':
        qry = """
            SELECT
                id as unique_id,
                'brand' as item_type,
                restaurant as name,
                case when restaurant = %(search_qry)s then 0 else 1 end as order
            FROM food_restaurants
            WHERE restaurant like %(search_qry_like)s
            ORDER BY case when restaurant = %(search_qry)s then 0 else 1 end
            LIMIT 100
        """
        results =  pd.read_sql(sql=qry, params={'search_qry':search_qry, 'search_qry_like':search_qry+"%"}, con=connection)
    else:
        # Default is 'food'
        qry = """
            SELECT
                food_key as unique_id,
                'food' as item_type,
                concat(food_description, ', ' ,brand) as name,
                case when food_description = %(search_qry)s then 0 else 1 end as order
            FROM food_foods
            WHERE food_description like %(search_qry_like)s
            ORDER BY case when food_description = %(search_qry)s then 0 else 1 end
            LIMIT 100
        """
        results =  pd.read_sql(sql=qry, params={'search_qry':search_qry, 'search_qry_like':search_qry+"%"}, con=connection)
    results_dict = results.to_dict('records')
    return Response({'menu_search_results': results_dict})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_menu_item(request):
    post_data = request.data["params"]
    menu_id = post_data["menu_id"]
    unique_id = post_data["unique_id"]
    item_type = post_data["item_type"]
    meal_type = post_data["meal_type"]
    dish_num = post_data["dish_num"].replace('_',' ').title()
    if item_type=='food':
        # check if exists
        FoodPreferences.objects.get_or_create(meal_type=meal_type, dish_num=dish_num,prefmenu_id=menu_id, food_id=unique_id)
    elif item_type=='meal':
        MealPreferences.objects.get_or_create(meal_type=meal_type, dish_num=dish_num,prefmenu_id=menu_id, meal_id=unique_id)
    elif item_type=='tag':
        FoodTagPreferences.objects.get_or_create(meal_type=meal_type, dish_num=dish_num,prefmenu_id=menu_id, tag_id=unique_id)
    elif item_type=='restaurant':
        RestaurantPreferences.objects.get_or_create(meal_type=meal_type, dish_num=dish_num,prefmenu_id=menu_id, meal_id=unique_id)
    return Response({"status":"success"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_menu_item(request):
    post_data = request.data["params"]
    menu_id = post_data["menu_id"]
    unique_id = post_data["unique_id"]
    item_type = post_data["item_type"]
    meal_type = post_data["meal_type"]
    dish_num = post_data["dish_num"].replace('_',' ').title()
    if item_type=='food':
        FoodPreferences.objects.filter(meal_type=meal_type, dish_num=dish_num,prefmenu_id=menu_id, food_id=unique_id).delete()
    elif item_type=='meal':
        MealPreferences.objects.filter(meal_type=meal_type, dish_num=dish_num,prefmenu_id=menu_id, meal_id=unique_id).delete()
    elif item_type=='tag':
        FoodTagPreferences.objects.filter(meal_type=meal_type, dish_num=dish_num,prefmenu_id=menu_id, tag_id=unique_id).delete()
    elif item_type=='restaurant':
        RestaurantPreferences.objects.filter(meal_type=meal_type, dish_num=dish_num,prefmenu_id=menu_id, meal_id=unique_id).delete()
    else:
        print(post_data)
    return Response({"status":"success"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_food_max_servings(request):
    post_data = request.data["params"]
    food_key = post_data["food_key"]
    user_prob,_ = UserProbRejectFood.objects.get_or_create(user_id=request.user.id, food_id=food_key) # Create if doesn't exist
    try: 
        maxServings = int(post_data["maxServings"])
        user_prob.max_servings =maxServings
        user_prob.save()
        status = "success"
    except:
        status = "failed"
    return Response({"status":"status"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_initial_menu_options(request):
    """
    Runs When Browse And Build Menus Renders
    """
    menu_opts_qry = """
        SELECT
            m.*,
            'public' as menu_type,
            pp.user_id,
            pp.avatar,
            pp.preferred_name
        FROM core_publicmenu m
        LEFT JOIN core_personalprofile pp
            ON m.create_user_id = pp.user_id
        ORDER BY total_clones
        LIMIT 10
    """
    menus_df = pd.read_sql(sql=menu_opts_qry,con=connection)
    menus_df = menus_df.fillna(0)
    menus_list = menus_df.to_dict('records')
    # Pulling the first object for the first preview
    first_menu_id = menus_list[0]['id']
    public_menu = PublicMenu.objects.get(id=first_menu_id)
    params={'user_id':public_menu.create_user_id, 'prefmenu_id_list':(public_menu.breakfast_prefmenu_id,public_menu.lunch_prefmenu_id,public_menu.dinner_prefmenu_id,public_menu.snack_prefmenu_id)}
    menu_dict = query_menus(params)
    pref_menu_dict = {'Breakfast':{'id':public_menu.breakfast_prefmenu_id},
                     'Lunch':{'id':public_menu.lunch_prefmenu_id},
                     'Dinner':{'id':public_menu.dinner_prefmenu_id},
                     'Snack':{'id':public_menu.snack_prefmenu_id}}
    return Response({'menus_list':menus_list,'menu_dict':menu_dict, 'pref_menu_dict':pref_menu_dict})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_starter_menus(request):
    """
    Get all menus shown in the onboarding process. HARD-CODED here
    """
    # Menus
    post_data = request.data["params"]
    sugg_menu = post_data['sugg_menu']
    menu_opts_qry = """
        SELECT
            m.*,
            'public' as menu_type,
            pp.user_id,
            pp.avatar,
            pp.preferred_name
        FROM core_publicmenu m
        LEFT JOIN core_personalprofile pp
            ON m.create_user_id = pp.user_id
        WHERE m.id in (2,4,5)
        ORDER BY CASE WHEN m.id = %(start_id)s then 0 else 1 end
    """
    params = {'start_id':sugg_menu}
    menus_df = pd.read_sql(sql=menu_opts_qry, params=params, con=connection)
    menus_df = menus_df.fillna(0)
    menus_list = menus_df.to_dict('records')
    # Get initial menu
    first_menu_id = menus_list[0]['id']
    public_menu = PublicMenu.objects.get(id=first_menu_id)
    params={'user_id':public_menu.create_user_id, 'prefmenu_id_list':(public_menu.breakfast_prefmenu_id,public_menu.lunch_prefmenu_id,public_menu.dinner_prefmenu_id,public_menu.snack_prefmenu_id)}
    menu_dict = query_menus(params)
    pref_menu_dict = {'Breakfast':{'id':public_menu.breakfast_prefmenu_id},
                     'Lunch':{'id':public_menu.lunch_prefmenu_id},
                     'Dinner':{'id':public_menu.dinner_prefmenu_id},
                     'Snack':{'id':public_menu.snack_prefmenu_id}}
    return Response({'menus_list':menus_list,'menu_dict':menu_dict, 'pref_menu_dict':pref_menu_dict})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_initial_menu_options_user_only(request):
    """
    Runs When Edit Menus Page Renders
    """
    menu_opts_qry = """
        SELECT
            m.*,
            'public' as menu_type,
            pp.user_id,
            pp.avatar,
            pp.preferred_name
        FROM core_publicmenu m
        LEFT JOIN core_personalprofile pp
            ON m.create_user_id = pp.user_id
        WHERE m.create_user_id=%(user_id)s
        ORDER BY total_clones
        LIMIT 10
    """
    params={'user_id':request.user.id}
    menus_df = pd.read_sql(sql=menu_opts_qry,params=params,con=connection)
    # if menus_df.empty:
    #     return Response({'no_results':True})
    menus_df = menus_df.fillna(0)
    menus_list = menus_df.to_dict('records')
    #Not returning Usermenu becasue the get / set methods are all based on public menu. But might be a bad user exp.
    default_menu_qry = """
        SELECT
            m.*,
            'personal' as menu_type,
            pp.preferred_name || 's Personal Menu' as menu_name,
            'The personal menu for ' || pp.preferred_name || '. This menu powers your autoplanner recommendations and cannot be made public.' as menu_description,
            cast(0 as int) as total_clones,
            pp.user_id,
            pp.avatar,
            pp.preferred_name
        FROM core_usermenu m
        LEFT JOIN core_personalprofile pp
            ON m.user_id = pp.user_id
        WHERE m.user_id=%(user_id)s
        LIMIT 1
    """# LIMIT 1 IS A FAILSAFE, SHOULD NOT BE NECESSARY
    def_menus_df = pd.read_sql(sql=default_menu_qry,params=params,con=connection)
    def_menus_df = def_menus_df.fillna(0)
    menus_list = def_menus_df.to_dict('records') + menus_list
    #Pulling the first object for the first preview
    first_menu_id = menus_list[0]['id'] # should always be user's default
    user_menu = UserMenu.objects.get(id=first_menu_id)
    params={'user_id':user_menu.user_id, 'prefmenu_id_list':(user_menu.breakfast_prefmenu_id,user_menu.lunch_prefmenu_id,user_menu.dinner_prefmenu_id,user_menu.snack_prefmenu_id)}
    menu_dict = query_menus(params)
    pref_menu_dict = {'Breakfast':{'id':user_menu.breakfast_prefmenu_id},
                     'Lunch':{'id':user_menu.lunch_prefmenu_id},
                     'Dinner':{'id':user_menu.dinner_prefmenu_id},
                     'Snack':{'id':user_menu.snack_prefmenu_id}}
    return Response({'no_results':False, 'menus_list':menus_list,'menu_dict':menu_dict, 'pref_menu_dict':pref_menu_dict})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_public_menu_from_id(request):
    """
    Get all menu items from a public menu id
    """
    post_data = request.data["params"]
    pub_menu_id = post_data["id"]
    user_id = post_data["user_id"]
    menu_type = post_data["menu_type"]
    if menu_type=='public':
        public_menu = PublicMenu.objects.get(id=pub_menu_id)
    else:
        public_menu = UserMenu.objects.get(id=pub_menu_id)
    params={'user_id':user_id, 'prefmenu_id_list':(public_menu.breakfast_prefmenu_id,public_menu.lunch_prefmenu_id,public_menu.dinner_prefmenu_id,public_menu.snack_prefmenu_id)}
    menu_dict = query_menus(params)
    pref_menu_dict = {'Breakfast':{'id':public_menu.breakfast_prefmenu_id},
                     'Lunch':{'id':public_menu.lunch_prefmenu_id},
                     'Dinner':{'id':public_menu.dinner_prefmenu_id},
                     'Snack':{'id':public_menu.snack_prefmenu_id}}
    return Response({'menu_dict':menu_dict, 'pref_menu_dict':pref_menu_dict})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_user_menu_from_id(request):
    return Response({})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def new_public_menu(request):
    """
    Save A New Menu Without A Current Id
    """
    post_data = request.data["params"]
    menu_name = post_data["menu_name"]
    menu_description = post_data["menu_description"]
    breakfast_prefmenu = PrefMenu.objects.create(create_user_id=request.user.id,
                                                user_id=request.user.id,
                                                default_flg=False,
                                                menu_name=menu_name,
                                                reusable_flg=True,
                                                public_flg=True,
                                                meal_type='Breakfast')
    lunch_prefmenu = PrefMenu.objects.create(create_user_id=request.user.id,
                                                user_id=request.user.id,
                                                default_flg=False,
                                                menu_name=menu_name,
                                                reusable_flg=True,
                                                public_flg=True,
                                                meal_type='Lunch')
    dinner_prefmenu = PrefMenu.objects.create(create_user_id=request.user.id,
                                                user_id=request.user.id,
                                                default_flg=False,
                                                menu_name=menu_name,
                                                reusable_flg=True,
                                                public_flg=True,
                                                meal_type='Dinner')
    snack_prefmenu = PrefMenu.objects.create(create_user_id=request.user.id,
                                                user_id=request.user.id,
                                                default_flg=False,
                                                menu_name=menu_name,
                                                reusable_flg=True,
                                                public_flg=True,
                                                meal_type='Snack')
    public_menu = PublicMenu.objects.create(create_user_id=request.user.id, 
                                            menu_name=menu_name,
                                            menu_description=menu_description,
                                            breakfast_prefmenu_id=breakfast_prefmenu.id, 
                                            lunch_prefmenu_id=lunch_prefmenu.id,
                                            dinner_prefmenu_id=dinner_prefmenu.id,
                                            snack_prefmenu_id=snack_prefmenu.id)
    pref_menu_dict = {'Breakfast':{'id':public_menu.breakfast_prefmenu_id},
                     'Lunch':{'id':public_menu.lunch_prefmenu_id},
                     'Dinner':{'id':public_menu.dinner_prefmenu_id},
                     'Snack':{'id':public_menu.snack_prefmenu_id}}
    return Response({'menu_id':public_menu.id, 'pref_menu_dict':pref_menu_dict})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clone_public_menu(request):
    """
    Clones a publicmenu object to a user's menu. Should include a temporary storage solution for undo option
    """
    meals = ['breakfast', 'lunch','dinner','snack']
    post_data = request.data["params"]
    menu_id = post_data["menu_id"]
    overwrite = post_data["overwrite"]
    print(overwrite)
    return_menu = post_data["return_menu"]
    public_menu = PublicMenu.objects.get(id=menu_id)
    # Updating n clones metadata
    public_menu.total_clones += 1
    public_menu.current_clones += 1
    public_menu.save()
    user_menu = UserMenu.objects.get(user_id=request.user.id)
    curr_clone_id = user_menu.cloned_from_id
    if curr_clone_id:
        curr_clone_menu = PublicMenu.objects.get(id=curr_clone_id)
        curr_clone_menu.current_clones -= 1
        curr_clone_menu.save()
    user_menu.cloned_from_id = public_menu.id
    user_menu.clone_date = datetime.date.today()
    user_menu.save()
    for meal in meals:
        pub_prefmenu_id = getattr(public_menu, meal+'_prefmenu_id')
        usr_prefmenu_id = getattr(user_menu, meal+'_prefmenu_id')
        if overwrite:
            #PrefMenu.objects.filter(id=usr_prefmenu_id).delete()
            FoodPreferences.objects.filter(prefmenu_id=usr_prefmenu_id).delete()
            MealPreferences.objects.filter(prefmenu_id=usr_prefmenu_id).delete()
            RestaurantPreferences.objects.filter(prefmenu_id=usr_prefmenu_id).delete()
            FoodTagPreferences.objects.filter(prefmenu_id=usr_prefmenu_id).delete()

        pub_food_prefs = FoodPreferences.objects.filter(prefmenu_id=pub_prefmenu_id)
        for food_pref in pub_food_prefs:
            FoodPreferences.objects.create(prefmenu_id=usr_prefmenu_id, 
                                    meal_type=food_pref.meal_type,
                                    dish_num=food_pref.dish_num,
                                    food_id=food_pref.food_id)

        pub_meal_prefs = MealPreferences.objects.filter(prefmenu_id=pub_prefmenu_id)
        for meal_pref in pub_meal_prefs:
            MealPreferences.objects.create(prefmenu_id=usr_prefmenu_id,
                                    meal_type=meal_pref.meal_type,
                                    dish_num=meal_pref.dish_num,
                                    meal_id=meal_pref.meal_id)

        pub_rest_prefs = RestaurantPreferences.objects.filter(prefmenu_id=pub_prefmenu_id)
        for rest_pref in pub_rest_prefs:
            RestaurantPreferences.objects.create(prefmenu_id=usr_prefmenu.id,
                                        meal_type=rest_pref.meal_type,
                                        dish_num=rest_pref.dish_num,
                                        restaurant_id=rest_pref.restaurant_id)

        pub_tag_prefs = FoodTagPreferences.objects.filter(prefmenu_id=pub_prefmenu_id)
        for tag_pref in pub_tag_prefs:
            FoodTagPreferences.objects.create(prefmenu_id=usr_prefmenu_id,
                                        meal_type=tag_pref.meal_type,
                                        dish_num=tag_pref.dish_num,
                                        tag_id=tag_pref.tag_id)

    if not return_menu:
        return Response({'status':'success'})
    else:
        print("Getting menu to return")
        menu_params ={'user_id':request.user.id, 
                        'prefmenu_id_list':(user_menu.breakfast_prefmenu_id,user_menu.lunch_prefmenu_id,user_menu.dinner_prefmenu_id,user_menu.snack_prefmenu_id)}
        menu_dict = query_menus(menu_params)
        return Response({'status':'success', 'menu_dict':menu_dict})

#   ***
#   NUTRIENTS
#   ***

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_nutrient(request):
    """
    Updates a single_nutrient
    """
    post_data = request.data['params']
    nut_abrev = post_data["nut_abrev"]
    req_list = post_data["req_list"]
    prof = Profile.objects.get(user=request.user)
    setattr(prof, nut_abrev+"_lb", req_list[0])
    setattr(prof, nut_abrev+"_ub", req_list[1])
    prof.save()
    return Response({"status":"success"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_nutrients(request):
    """
    Updates all nutrients
    """
    post_data = request.data['params']
    requirements_dict = post_data["requirements_dict"]
    prof = Profile.objects.get(user=request.user)
    for nut_abrev in nut_abrev_list:
        if nut_abrev+"_lb" in requirements_dict:
            setattr(prof, nut_abrev+"_lb", requirements_dict[nut_abrev+"_lb"])
            prof.save()
            setattr(prof, nut_abrev+"_ub", requirements_dict[nut_abrev+"_ub"])
            prof.save()
    prof.save()
    return Response({"status":"success"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_user_stats(request):
    """
    Updates user stats
    """
    post_data = request.data['params']
    user_stats = post_data["user_stats"]
    prof = Profile.objects.get(user=request.user)
    prof.weight = user_stats["weight"]
    prof.weight_unit = user_stats["weight_unit"]
    prof.height_feet = user_stats["height_feet"]
    prof.height_inches = user_stats["height_inches"]
    prof.age = user_stats["age"]
    prof.sex = user_stats["sex"]
    prof.activity = user_stats["activity"]
    prof.cal_adj = user_stats["cal_adj"]
    prof.pro_perc = user_stats["pro_perc"]
    prof.fat_perc = user_stats["fat_perc"]
    prof.car_perc = user_stats["car_perc"]
    prof.save()
    return Response({"status":"success"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_macro_perc(request):
    """
    Updates user stats
    """
    post_data = request.data['params']
    prof = Profile.objects.get(user=request.user)
    prof.pro_perc = post_data["pro_perc"]
    prof.fat_perc = post_data["fat_perc"]
    prof.car_perc = post_data["car_perc"]
    prof.pro_ub = post_data["pro_ub"]
    prof.fat_ub = post_data["fat_ub"]
    prof.car_ub = post_data["car_ub"]
    prof.pro_lb = post_data["pro_lb"]
    prof.fat_lb = post_data["fat_lb"]
    prof.car_lb = post_data["car_lb"]
    prof.save()
    return Response({"status":"success"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_default_req(request):
    """
    Updates Default Nutrient
    """
    post_data = request.data['params']
    nut_abrev = post_data['nut_abrev']
    new_bool = post_data['new_bool']
    prof = Profile.objects.get(user_id=request.user.id)
    setattr(prof, nut_abrev, new_bool)
    prof.save()
    return Response({'status':'success'})


"""
@api_view(['POST'])
def get_conf_email(request):
    serialized = UserSerializer(data=request.data)
    if serialized.is_valid():
        # Send email
        send_mail(
            subject="Please Confirm Your Email For PlanYourMeals.com",
            message="test",
            from_email="confirm@planyourmeals.com",
            recipient_list=[serialized.data['email']],
            fail_silently=False
            )
        return Response({"message":"Confirmation sent"}, status=status.HTTP_201_CREATED)
    else:
        return Response(serialized._errors, status=status.HTTP_400_BAD_REQUEST)
"""
"""
@api_view(['POST'])
def create_auth(request):
    serialized = UserSerializer(data=request.data)
    if serialized.is_valid():
        # Send email
        serialized.create(request.data)
        return Response(serialized.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serialized._errors, status=status.HTTP_400_BAD_REQUEST)
"""
#   ***
#   PROFILE
#   ***
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_personal_profile(request):
    """
    Gets personal info for profile page on load.
    """
    prof_qry = """
        SELECT
            pp.*,
            u.first_name,
            u.last_name
        FROM core_personalprofile pp
        JOIN auth_user u
            ON pp.user_id = u.id
            AND pp.user_id = %(user_id)s
    """
    personal_profile = pd.read_sql(sql=prof_qry,params={'user_id':request.user.id},con=connection)
    prof_dict = personal_profile.to_dict('records')[0]
    # Is surprisingly more complicated. Is quite the query. Will need to group by planmeal and sum up calories and macros and compare to current requirements.
    # Am not saving past requirements, so the streak cannot be verfiied. 
    streak_qry="""
        SELECT
            pm,
            pm.id,
            m.id,
        FROM plan_planmeal pm
        JOIN plan_meal m 
            ON pm.meal_id = m.id
        JOIN plan_food_amount am
            ON m.id=am.meal_id
        WHERE pm.user_id = %(user_id)s
    """
    return Response({'prof_dict':prof_dict})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_personal_profile(request):
    """
    """
    post_data = request.data['params']
    item_key = post_data['item_key']
    item_value = post_data['item_value']
    prof = PersonalProfile.objects.get(user_id=request.user.id)
    setattr(prof, item_key, item_value)
    prof.save()
    return Response({item_key:item_value})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_profile_photo(request):
    """
    Updates personal profile photo
    """
    image_file = request.FILES['profile_image'].read()
    user_id = request.user.id
    s3_client = boto3.client('s3',
        aws_access_key_id=AK,
        aws_secret_access_key=SAK,
    )
    avatar = "https://planyourmealsmedia.s3.amazonaws.com/profile/"+str(user_id)+"/thumbnail.png"
    prof = PersonalProfile.objects.get(user_id=request.user.id)
    prof.avatar = avatar
    prof.save()
    result = s3_client.put_object(Bucket="planyourmealsmedia",Body=image_file,Key="profile/"+str(user_id)+"/thumbnail.png")
    return Response({'avatar':avatar})

#   ***
#   PAYMENT
#   ***

def get_membership_message(status, start_date):
    if status == 'full':
        message = 'You are subscribed. Your membership will renew for $9.00 at the start of the month.'
        free_trial_days = 0
    elif status == 'free':
        message = 'Your free trial has expired. Subscribe below for full access at only $9.00 a month.'
        free_trial_days = 0
    else:
        free_trial_days = max([7 - (datetime.date.today()-tart_date).days, 0])
        message = f"You have {str(free_trial_days)} days left in your free trial."

@api_view(['POST'])
def load_membership(request):
    """
    Loads membership status, user email, and membership message (such as '7 days left in your free trial') whenever a user access the account page
    Options for membership message:
        * You have (n>0) days left in your free trial.
        * Your free trial has expired. Please subscribe for full access. 
        * You are subscribed. Your membership will renew at the start of the month. 
    """
    post_data = request.data['params']
    user_info = User.objects.get(id=request.user.id)
    user_acct = UserAccount.objects.get(user_id=request.user.id)
    if user_acct.status == 'full':
        message = 'You are subscribed. Your membership will renew for $9.00 at the start of the month.'
        free_trial_days = 0
    elif user_acct.status == 'free':
        message = 'Your free trial has expired. Subscribe below for full access at only $9.00 a month.'
        free_trial_days = 0
    else:
        free_trial_days = max([7 - (datetime.date.today()-user_acct.trial_start_date).days, 0])
        message = f"You have {str(free_trial_days)} days left in your free trial."
    resp_dict = {
        'email':user_info.email,
        'status':user_acct.status,
        'membership_message': message,
        'free_trial_days': free_trial_days
    }
    return Response(resp_dict)


@api_view(['GET','POST'])
def setup_payment(request):
    """
    Sends payment info to stripe, returns success message. If successful, switches membership to 
    """
    # post_data = request.data['params']
    # logging.info(request)
    try:

        post_data = request.data
        reactivate = post_data['reactivate'] # true of false. If false, start 7-day free trial
        payment_method = post_data['payment_method'] # created via Stripe API on front-end
        plan_id = post_data['plan_id'] # created via Stripe API on front-end
        # logging.info("Unpacked parameters successfully")
        # Add API key to imported stripe obj
        stripe.api_key = STRIPE_API_KEY
        # Create / get stripe customer
        # user = User.objects.get(id=request.user.id)
        # email = user.email
        email = post_data['email']
        cust_acct = UserAccount.objects.get(user_id=request.user.id) # get or create just in case
        if cust_acct.stripe_cust_id:
            stripe_cust_id = cust_acct.stripe_cust_id
        else:
            # logging.info("Creating Customer")
            customer = stripe.Customer.create(
                    payment_method=payment_method,
                    email=email,
                    invoice_settings={
                        'default_payment_method':payment_method
                    }
                )
            stripe_cust_id = customer.id
            cust_acct.stripe_cust_id = stripe_cust_id
            cust_acct.save()
        # Start subscription. Not passing in billing_cycle_anchor, so all should default to last day of month
        # if reactivate:
            # activate starting now
            # logging.info("Creating subscription")
        subscription = stripe.Subscription.create(
                    customer=stripe_cust_id,
                    items=[
                    {
                        'plan': plan_id,
                    },],
                    expand=['latest_invoice.payment_intent'],
        )
            # logging.info("subscription created")
        # else:
        #     # activate 7-day trial
        #     trial_start = datetime.datetime.now()
        #     cust_acct.trial_start_date = trial_start
        #     trial_end = trial_start + datetime.timedelta(days=7)
        #     trial_end_utc = int(trial_end.timestamp())
        #     subscription = stripe.Subscription.create(
        #             customer=stripe_cust_id,
        #             items=[
        #             {
        #             'plan': plan_id,
        #             },
        #             ],
        #             expand=['latest_invoice.payment_intent'],
        #             trial_end=trial_end_utc,
        #     )
        cust_acct.status='full'
        cust_acct.stripe_sub_id = subscription.id
        cust_acct.status_start_date = datetime.date.today()
        cust_acct.save()
        # TODO - Needs to send email to customer
        send_mail(subject="Subscription Confirmation",
                message="""
                    Your subscription to Planyourmeals.com has been activated! If you have any feedback, requests, complaints or just need help please reach out to 
                    me at planyourmealsguy@gmail.com. My number one priority is helping you reach your goals! \n

                    James
                    """,
                from_email="confirm@planyourmeals.com",
                recipient_list=[email],
                )
        resp = {'message': "Subscription successful!"}
        resp['status'] = cust_acct.status
        resp['email'] = email
        resp['free_trial_days'] = 0
        resp['membership_message'] = 'You are subscribed. Your membership will renew for $9.00 at the start of the month.'
        return Response(resp) # maybe subscription status and next charge date

    except Exception as e:
        # logging.info(f"Stripe payment error for user_id {str(request.user.id)}")
        # logging.info(e)

        send_mail(subject="Subscription Confirmation",
                message=f"""
                    Stripe issue for customer {str(cust_acct.user_id)} \n
                    Stripe account error: {e}
                    """,
                from_email="confirm@planyourmeals.com",
                recipient_list=['james.dvance@gmail.com'],
                )
        return Response({"message": "There was an error. Please contact support"})


# Cancel
@api_view(['POST'])
def cancel_subscription(request):
    """
    Cancels subscription payment
    """
    post_data = request.data
    if (UserAccount.objects.filter(user_id=request.user.id).exists() and not UserAccount.objects.get(user_id=request.user.id).always_full ):
        user_acct =  UserAccount.objects.get(user_id=request.user.id)
        stripe.api_key = STRIPE_API_KEY
        stripe_sub_id = user_acct.stripe_sub_id
        stripe.Subscription.delete(stripe_sub_id)
        # set status_start_date to null and set status_end_date to 
        start_date = user_acct.status_start_date
        today = datetime.date.today()
        if start_date.day > today.day: # to expire later this month
            if start_date.day <28:
                end_date = datetime.date(today.year, today.month, start_date.day)
            else:
                end_date = datetime.date(today.year, today.month, 28)
        else: # status to exire next month
            if start_date.day <28:
                end_date = datetime.date(today.year, today.month+1, start_date.day)
            else:
                end_date = datetime.date(today.year, today.month+1, 28)

        user_acct.status_start_date = None
        user_acct.status_end_date = end_date
        user_acct.save()
        user=User.objects.get(id=request.user.id)
        send_mail(subject="Cancelation Confirmation",
                message=f"""
                    Your subscription to Planyourmeals.com has been canceled. Your membership will expire on {str(end_date)}. We'd love to have your feedback! Please message planyourmealsguy@gmail.com with any
                    feedback, requests or complaints. We'd love to have you join us again but either way best of luck in your health journey! 
                    """,
                from_email="confirm@planyourmeals.com",
                recipient_list=[user.email],
                )
        # TODO - return the updated status
        resp = {'message':f"Subscription successfully canceled! You will continue to have access until {str(end_date)}", 'outcome':'success'}
        resp['status'] = user_acct.status
        resp['email'] = user.email
        resp['free_trial_days'] = 0
        resp['membership_message'] = f"You have canceled your membership. You will continue to have full access until {str(end_date)}."
        return Response(resp)
    else:
        resp = {'message':"No Account Info Saved Or This User Has An Ongoing Coupon", 'outcome':'fail'}
        return Response(resp)

#   ***
#   LEADS
#   ***
@api_view(['POST'])
def save_email_lead(request):
    post_data = request.data['params']
    email = post_data["email"]
    source = post_data["source"]
    email, _ = EmailLeads.objects.get_or_create(email=email, source=source)
    return Response({})

#   ***
#   MESSAGES
#   ***

@api_view(['POST'])
def save_user_message(request):
    """
    Saves user message from front-end
    """ 
    post_data = request.data['params']
    user_email = User.objects.get(id=request.user.id).email
    message_type = post_data['message_type']
    message = post_data['message']
    user_message = UserMessage.objects.create(user=request.user, message_type=message_type, message_text=message)
    # Send confirmation email
    send_mail(subject="Your Message To PlanYourMeals was Recieved",
                message="We'll reply shortly. Thanks for your feedback!",
                from_email="confirm@planyourmeals.com",
                recipient_list=[user_email],
                )
    # Send admin email
    admin_message = f"User's email: {user_email} \n User's message: {message} \n "
    send_mail(subject="New User Message From PlanYourMeals.com",
                message=admin_message,
                from_email="confirm@planyourmeals.com",
                recipient_list=["planyourmealsguy@gmail.com"],
                )
    return Response({"status":"success"})

#   ***
#   BLOG
#   ***

def blog_input(request):
    # display django form
    if request.method == 'POST':
        form = BlogForm(request.POST)
        if form.is_valid():
            return HttpResponseRedirect('/blog/blog_input/')
    else:
        form=BlogForm()
    return render(request, 'blog_input.html', {'form':form})

# @api_view(['POST'])
def blog_input_search(request):
    print(request.POST.get('params'))
    qry = request.POST.get('search_qry')
    # qry=request.data['params']["search_qry"]
    print(request.POST)
    blogs = Blog.objects.filter(title__contains=qry)
    blogs_ser = serializers.serialize('python',blogs)
    return JsonResponse({'blog_list':blogs_ser})

@api_view(['POST'])
def blog_search(request):
    return Response({})

@api_view(['POST'])
def blog_post(request):
    return Response({})