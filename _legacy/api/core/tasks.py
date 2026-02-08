import datetime
from django.db.models import Count
from django.db import connection
from django.core.mail import send_mail
from celery import shared_task
#import logging
#logging.basicConfig(filename='../celery/tasks.log',level=logging.INFO)
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)
from django.contrib.auth.models import User
from core.models import UserProbRejectFood, UserProbRejectMeal, GlobalProbRejectFood, GlobalProbRejectMeal, PersonalProfile, UserAccount
from plan.models import PlanMeal, Meal, Food_Amount, EmailLeads
from food.models import Foods

@shared_task
def test_minute_task(name='core.tasks.test_minute_task'):
	logger.info("running test task")
	text_file = open('/var/www/planyourmealsapi/cron_test.txt', 'w')
	text_file.write('Writing Every Minute')
	text_file.close()
	EmailLeads.objects.get_or_create(email='prod_test@test.com', source='prod_celery_testing')
	return

@shared_task(name='core.tasks.save_prob_r_total_used')
def save_prob_r_total_used(name='core.tasks.save_prob_r_total_used'):
	"""
	Saves if foods still in plan on each day. Increments 'n_uses' or creates new record with 'n_uses' = 1
	And 'last use'
	Runs daily
	"""
	print("running save prob r total used")
	run_date = datetime.date.today() - datetime.timedelta(days=1) # Will be run morning after each day
	today_plans = PlanMeal.objects.filter(plan_date=run_date) # pulling for all users at once
	logger.info(f"Updating prob_r tables for {str(run_date)}. Incrementing for {str(len(today_plans))} plans.")
	for plan_meal in today_plans:
		food_amounts = Food_Amount.objects.filter(meal_id=plan_meal.meal_id)
		for food in food_amounts:
			food_prob_r, created = UserProbRejectFood.objects.get_or_create(user_id=plan_meal.user_id, food_id=food.food_id)
			curr_uses = food_prob_r.user_total_uses
			food_prob_r.user_total_uses = curr_uses + 1
			food_prob_r.last_use = run_date
			if food_prob_r.last_view != run_date:
				food_prob_r.last_view = run_date
				food_prob_r.viewed += 1
			food_prob_r.save()
			logger.info(f"Updated curr uses for food id {str(food.food_id)} from {str(curr_uses)} to {str(food_prob_r.user_total_uses)}.")
		if plan_meal.meal_source:
			meal_prob_r, created = UserProbRejectMeal.objects.get_or_create(user_id=plan_meal.user_id, meal_id=plan_meal.meal_source)
			curr_uses = meal_prob_r.user_total_uses
			meal_prob_r.user_total_uses = curr_uses + 1
			meal_prob_r.last_use = run_date
			meal_prob_r.last_use = run_date
			if meal_prob_r.last_view != run_date:
				meal_prob_r.last_view = run_date
				meal_prob_r.viewed += 1
			meal_prob_r.save()
			logger.info(f"Updated curr uses for meal id {str(plan_meal.meal_source)} from {str(curr_uses)} to {str(meal_prob_r.user_total_uses)}.")
	return

@shared_task(name='core.tasks.update_account_status')
def update_account_status(name='core.tasks.update_account_status'):
	"""
	Runs daily and updates user account status
	"""
	logger.info("Checking for expired trial accounts")
	expired_trial_date = datetime.date.today()-datetime.timedelta(days=7)
	accounts = UserAccount.objects.filter(status='trial', trial_start_date__lte=expired_trial_date)
	logger.info(f"Updating for {str(len(accounts))} accounts")
	for account in accounts:
		logger.info(f"Updating status to free from trial for user {str(account.user_id)} on {str(datetime.date.today())}")
		account.trial_completed=True
		account.status='free'
		account.save()
		# Trigger trial expiration email
		user = User.objects.get(id=account.user_id)
		send_mail(subject="Free Trial Expiration",
				message="""
					Your free trial for planyourmeals.com has expired. Don't worry - we still have all your saved plans and settings. Go to https://planyourmeals.com/account to subscribe for 
					full access!
				""",
				from_email="confirm@planyourmeals.com",
				recipient_list=[user.email]
			)
	# Add status switch for users who have unsubscribed
	canceled_accounts = UserAccount.objects.filter(status_end_date=datetime.date.today())
	for canceled_account in canceled_accounts:
		canceled_account.status='free'
		canceled_account.save()
		user = User.objects.get(id=account.user_id)
		send_mail(subject="Planyourmeals.com Membership Expiration",
				message="""
					Your membership for planyourmeals.com has expired. Don't worry - we still have all your saved plans and settings. Go to https://planyourmeals.com/account to subscribe for 
					full access. If we don't see you, good luck on your health journey! If so, please tell us what anything could be doing differently by emailing planyourmealsguy@gmail.com.
				""",
				from_email="confirm@planyourmeals.com",
				recipient_list=[user.email]
			)

def global_prob_reject_food():
	"""
	Updates global prob_reject_food by averaging each users' score
	Runs weekly
	"""
	update_qry ="""
		UPDATE  core_global_prop_reject_food
	"""
	# cursor = connection.cursor()
	# cursor.execute(update_qry)
	# cursor.commit()
	# cursor.close()

def global_prob_reject_meal():
	"""
	Updates global prob_reject_meal by averaging each user's score
	Runs weekly
	"""
	pass

@shared_task
def update_viewed_today(foods_list, user_id):
	"""
	Increments 'viewed' per meal or food and 'last_view'
	Is not scheduled. Runs asyncronously after autoplan returns.
	"""
	for food in foods_list:
		user_prob_r, created = UserProbRejectFood.objects.get_or_create(user_id=user_id, food_id=food['food_key'])
		last_view = user_prob_r.last_view
		if last_view != datetime.date.today():
			user_prob_r.viewed += 1 # only increment once a day
			user_prob_r.last_view = datetime.date.today()
			user_prob_r.save()
	return

@shared_task
def update_removed():
	update_prob_r_food_qry = """
		UPDATE core_userprobrejectfood
		
	"""

def update_user_streaks():
	"""
	Checks if each user met their requirements for the day in different categories and increments their scores or resets to zero. 
	Also updates a history table to be able to pull metrics
	Runs daily
	Would be a good stored procedure also
	"""
	pass
	# profiles = Profile.objects.all()
	# for profile in profiles:
	# 	plan = PlanMeal.objects.filter()
	# 	if plan.PlanMeal.objects.filter()


def generate_suggested_foods():
	"""
	Generate foods to be suggested to user.
	Can start with a simple heuristic like highest stars that the user has never seen. 
	And / or foods with tags that coincide with what the user has eaten but the user hasn't seen.
	Then can obviously move to a real recommenders
	"""
	pass

def update_avg_stars():
	"""
	Set the stars for each food to the average of the group
	"""
	pass

def update_prob_r_coefficients():
	"""
	Kicks off processes to re-train the prob_r coefficients for both plans and meals
	Would run monthly
	"""
	pass


# if __name__=="__main__":
# 	pass