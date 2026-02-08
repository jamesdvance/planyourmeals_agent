import os
from secrets import *

## Notation stands for an item defined in local / production

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
# This links to inside the 'mealmaker' project folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!


# SECURITY WARNING: don't run with debug turned on in production!

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_auth',
    'allauth',
    'allauth.account',
    'django_rest_passwordreset',
    'rest_auth.registration',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.reddit',
    'corsheaders',
    'food',
    'core',
    'plan',
    'django_celery_beat',
]

SITE_ID = 1

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'planyourmeals_api.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'planyourmeals_api.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'plmapi',
    'USER': 'james',
    'PASSWORD': 'v2nc3123',
    'HOST': 'plm-api-db.ctjitqpxi57z.us-east-1.rds.amazonaws.com',
    'PORT':'5432',
    }
}

# Rest Framework 

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES':(
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication'
        #'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES':(
    )
}

# Authentication
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend'
]

# Social Account Providers
SOCIALACCOUNT_PROVIDERS = {
    'facebook':{
        'METHOD':'oauth2',
        'SCOPE':['email','public_profile'],
        'AUTH_PARAMS': {'auth_type':'reauthenticate'},
        'INIT_PARAMS': {'cookie', True},
        'FIELDS':[
            'ids',
            'email',
            'first_name',
            'last_name',
            'verified',
            'gender'
        ],
        'EXCHANGE_TOKEN': True,
        'LOCAL_FUNC':'path.to.callable',
        'VERIFIED_EMAIL': False,
        'VERSION': 'v2.12',
    },
    'google': {
        'SCOPE': ['profile','email'],
        'AUTH_PARAMS':{
            'access_type':'online',
        }
    },
    'reddit':{
        'AUTH_PARAMS':{'duration':'permanent'},
        'SCOPE': ['identity','submit'],
        'USER_AGENT':'django:eyf-mMhMsZApAg:1.0 (by /u/redditisgoodforme)',
    }
}

#SOCIAL_AUTH_POSTGRES_JSONFIELD = True
# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ALLAUTH SETTINGS
EMAIL_CONFIRMATION_SIGNUP = True
LOGIN_REDIRECT_URL = '/'

# CORS
CORS_ORIGIN_WHITELIST = [
    "https://planyourmeals.com", # React in S3
    "https://plan.planyourmeals.com",
    "http://localhost:3000", # Local React Server
    "https://localhost:3000",
    "http://73.132.71.180:3000", # Home Apt React Server
    "http://73.132.71.180", # Home Apt - for postman
    "https://73.132.71.180", # Home Apt - for postman
    "http://71.178.212.3", # Pallas common area
    "https://71.178.212.3", # Pallas common area
    "http://68.225.34.179", # Eden roc cir apt.
    "https://68.225.34.179", # Eden roc cir apt.
]

# Email
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'email-smtp.us-east-1.amazonaws.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'AKIAQ6T2IO35P2U3ALSQ'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'confirm@planyourmeals.com'

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

# Media Files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

# Storage
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# # AWS_QUERYSTRING_AUTH=False
# # AWS_USE_S3_SSL =False
# AWS_ACCESS_KEY_ID = AK
# AWS_SECRET_ACCESS_KEY = SAK
# AWS_STORAGE_BUCKET_NAME = 'planyourmealsmedia'

# AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
# AWS_S3_OBJECT_PARAMETERS = {
#     'CacheControl': 'max-age=86400',
# }
# AWS_LOCATION = 'static'

# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, 'planyourmeals_api/static'),
# ]
# STATIC_URL = 'https://%s/%s/' % (AWS_S3_CUSTOM_DOMAIN, AWS_LOCATION)

# CELERY STUFF
BROKER_URL = 'amqp://plm_admin:34r55@localhost/'
CELERY_RESULT_BACKEND = 'rpc://plm_admin:34r55@localhost/'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'EST'