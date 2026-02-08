"""planyourmeals_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# django
from django.contrib import admin
from django.urls import path, re_path, include
from django.views.generic import TemplateView
# third party
#from allauth.account.views import ConfirmEmailView,
from rest_auth.registration.views import VerifyEmailView, RegisterView
from markdownx import urls as markdownx
# app
from plan import views as plan_views
from core import views as core_views
from food import views as food_views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    # Auth
    path('',include('django.contrib.auth.urls')),
    path('rest-auth/', include('rest_auth.urls')),
    path('rest-auth/registration/', include('rest_auth.registration.urls')),
    path('rest-auth/google/', core_views.GoogleLogin.as_view(), name='google_login'),
    re_path(r'^accounts/confirm-email/(?P<key>[-:\w]+)/$', core_views.ConfirmEmailView.as_view(), name='account_confirm_email'), # is this baked in?
    path('accounts/', include('allauth.urls')),
    path('rest-auth/facebook/', core_views.FacebookLogin.as_view()),
    path('rest-auth/facebook/connect/', core_views.FacebookConnect.as_view()),
    re_path(r'^api/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('bad_email_conf/', core_views.bad_email_conf),
    # Start
    path('plan/get_day_plan/', plan_views.get_day_plan),
    path('user/get_user_reqs_and_menus/', core_views.get_user_reqs_and_menus),
    path('user/autocomplete_menus/', core_views.autocomplete_menus),
    path('user/return_acct_status/', core_views.return_acct_status),
    path('core/close_onboarding/', core_views.close_onboarding),
    # Core
    path('core/update_nutrient/', core_views.update_nutrient),
    path('core/update_nutrients/', core_views.update_nutrients),
    path('core/update_user_stats/', core_views.update_user_stats),
    path('core/get_user_nut_reqs/', core_views.get_user_nut_reqs),
    path('core/search_menu_items/', core_views.search_menu_items),
    path('core/add_menu_item/', core_views.add_menu_item),
    path('core/remove_menu_item/', core_views.remove_menu_item),
    path('core/update_food_max_servings/', core_views.update_food_max_servings),
    path('core/update_macro_perc/', core_views.update_macro_perc),
    path('core/update_default_req/', core_views.update_default_req),
    path('core/get_initial_menu_options/', core_views.get_initial_menu_options),
    path('core/get_public_menu_from_id/', core_views.get_public_menu_from_id),
    path('core/new_public_menu/', core_views.new_public_menu),
    path('core/get_initial_menu_options_user_only/', core_views.get_initial_menu_options_user_only),
    path('core/clone_public_menu/', core_views.clone_public_menu),
    path('core/get_personal_profile/', core_views.get_personal_profile),
    path('core/update_personal_profile/', core_views.update_personal_profile),
    path('core/update_profile_photo/', core_views.update_profile_photo),
    path('core/save_user_message/', core_views.save_user_message),
    path('core/get_starter_menus/', core_views.get_starter_menus),
    # Food
    path('food/get_food_modal/', food_views.get_food_modal),
    path('food/get_tag_autocomplete/',food_views.get_tag_autocomplete),
    path('food/add_food_tag/', food_views.add_food_tag),
    path('food/remove_food_tag/', food_views.remove_food_tag),
    path('food/save_recipe/', food_views.save_recipe),
    path('food/save_recipe_image/', food_views.save_recipe_image),
    path('food/search_recipes_for_edit/', food_views.search_recipes_for_edit),
    path('food/get_recipe_for_edit/', food_views.get_recipe_for_edit),
    path('food/edit_recipe/', food_views.edit_recipe),
    # Search
    path('search/food_test/', plan_views.search_foods),   
    path('search/food/', plan_views.FoodSearchView.as_view()),  
    path('search/food_raw/', plan_views.search_foods_raw),
    path('search/meals/', plan_views.search_meals),
    # Plan
    path('plan/update_meal_from_list/',plan_views.update_meal_from_list),
    path('plan/update_week_from_list/',plan_views.update_week_from_list),
    path('plan/get_range_plan/', plan_views.get_range_plan),
    path('plan/clear_meals/', plan_views.clear_meals),
    path('plan/get_meal/', plan_views.get_meal),
    path('plan/save_meal/', plan_views.save_meal),
    path('plan/edit_meal/', plan_views.edit_meal),
    path('plan/get_shopping_list_from_plan/', plan_views.get_shopping_list_from_plan),
    # Autoplan
    path('autoplan/autoplan_week/',plan_views.autoplan_week),
    path('autoplan/auto_adjust_week/',plan_views.auto_adjust_week),
    path('autoplan/get_food_alternative/',plan_views.get_food_alternative),
    # Account
    path('account/load_membership/',core_views.load_membership),
    path('account/setup_payment/',core_views.setup_payment),
    path('account/cancel_subscription/',core_views.cancel_subscription),
    # Leads
    path('core/save_email_lead/',core_views.save_email_lead),
    # Blog
    path('blog/blog_input/',core_views.blog_input),
    path('blog/blog_search/',core_views.blog_search),
    path('blog/blog_input_search/',core_views.blog_input_search),
    path('blog/blog_post/',core_views.blog_post),
    path('markdownx/', include('markdownx.urls')),
]
