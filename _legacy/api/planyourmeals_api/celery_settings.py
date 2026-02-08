from __future__ import absolute_import, unicode_literals
import os
import sys
sys.path.append('../')
from secrets import CELERY_BROKER_STRING
from celery import Celery
from celery.schedules import crontab
#set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'planyourmeals_api.settings.production')
#os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1') # For Windows use only
app = Celery('planyourmeals_api', broker=CELERY_BROKER_STRING)
app.config_from_object('django.conf:settings', namespace='CELERY')
# load tasks from all registered apps
app.autodiscover_tasks()
#scheduler
beat_scheduler="django_celery_beat.schedulers:DatabaseScheduler" 

