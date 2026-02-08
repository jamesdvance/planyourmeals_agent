import datetime
from django.db import connection
from celery import shared_task
import sys
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)
from core.models import UserProbRejectFood, UserProbRejectMeal, GlobalProbRejectFood, GlobalProbRejectMeal, PersonalProfile
from plan.models import PlanMeal, Meal, Food_Amount, EmailLeads
from food.models import Foods

@shared_task
def update_default_dish():
	"""
	Sets default dish_num to the largest vote via people's preferences
	Runs weekly.
	"""
	update_qry = """
		UPDATE food_foods set
		  default_dish_num = subquery.default_dish_num
		FROM(
			SELECT
			  food_id, 
			  default_dish_num
			FROM(
				SELECT
				  food_id,
				  default_dish_num,
				  row_number() over(partition by food_id||default_dish_num order by total desc) as row_num
				FROM (
				    SELECT 
				      food_id,
				      default_dish_num,
				      count(*) AS TOTAL
				    FROM (
				      SELECT
				        food_id,
				        dish_num as default_dish_num
				      FROM core_foodpreferences
				      UNION
				      SELECT
				        food_id,
				        default_dish_num
				       FROM 
				        core_userprobrejectfood
				    ) bar
				    GROUP BY food_id,default_dish_num
				  ) as foo
			) as bar
		WHERE row_num =1
		) subquery

		WHERE food_foods.food_key = subquery.food_id;
	"""

def update_avg_serving_size():
	"""
	Saves serving size and serving size unit each time one is changed
	Not scheduled. Called on any change
	"""
	pass