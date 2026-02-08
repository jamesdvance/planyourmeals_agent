from planyourmeals_api.settings.base import *

DEBUG = True

INSTALLED_APPS += (
	'markdownx',
)

ALLOWED_HOSTS = ['http://127.0.0.1', '127.0.0.1:8000', '127.0.0.1','https://localhost:3000'] 

# Define media root as the full path to the directory where you'd like Django to store uploaded files
MEDIA_ROOT = "C:/Users/J/Desktop/Git_Repositories/planyourmeals_api/"

# Define media url as the base public url of that directory

# Local, non-AWS postgres db
'''
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join('C:/Users/J/Desktop/Git_Repositories/mealmaker/mm_sqlite/', 'db.sqlite3'),
    }
}
'''


# CELERY
#CELERY_BROKER_URL = '0.0.0.0:5672'