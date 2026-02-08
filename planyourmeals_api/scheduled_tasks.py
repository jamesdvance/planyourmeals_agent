import os
import sys
import pytz
import django
sys.path.append('C:/Users/J/Desktop/Git_Repositories/planyourmeals_api/')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'planyourmeals_api.settings.local')
django.setup()
from django_celery_beat.models import PeriodicTask, PeriodicTasks, CrontabSchedule
#from core.models import Profile

# Great Daily 3am task - 3am EST corresponds to 12am PST so should be least likely time people will be using

def schedule_test_every_minute():
	schedule,_ = CrontabSchedule.objects.get_or_create(
			minute='*',
			hour='*',
			day_of_week='*',
			day_of_month='*',
			month_of_year='*',
			timezone=pytz.timezone('EST')
		)
	PeriodicTask.objects.create(
		crontab=schedule,
		name='Test task every minute',
		task='core.tasks.test_minute_task'
		)
	

def schedule_daily_batch_3am():
	schedule,_ = CrontabSchedule.objects.get_or_create(
			minute='0',
			hour='3',
			day_of_week='*',
			day_of_month='*',
			month_of_year='*',
			timezone=pytz.timezone('EST')
		)
	PeriodicTask.objects.create(
		crontab=schedule,
		name='Updating prob r total uses',
		task=core.tasks.save_prob_r_total_used
		)

def schedule_daily_batch_3_15am():
	schedule,_ = CrontabSchedule.objects.get_or_create(
			minute='15',
			hour='3',
			day_of_week='*',
			day_of_month='*',
			month_of_year='*',
			timezone=pytz.timezone('EST')
		)
	PeriodicTask.objects.create(
		crontab=schedule,
		name='Batch 3:15am',
		task=core.tasks.update_account_status
		)

def schedule_daily_batch_3_30am():
	schedule,_ = CrontabSchedule.objects.get_or_create(
			minute='30',
			hour='3',
			day_of_week='*',
			day_of_month='*',
			month_of_year='*',
			timezone=pytz.timezone('EST')
		)
	PeriodicTask.objects.create(
		crontab=schedule,
		name='Batch 3:30am',
		task=core.tasks.update_account_status
		)


if __name__=="__main__":
	#pass
	schedule_test_every_minute()
	#schedule_daily_batch_3am()