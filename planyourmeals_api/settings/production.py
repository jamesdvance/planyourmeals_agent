from planyourmeals_api.settings.base import *

DEBUG = False

INSTALLED_APPS += (
	
)

ALLOWED_HOSTS = ['api.planyourmeals.com', '18.208.208.235', 'ec2-18-208-208-235.compute-1.amazonaws.com', '169.254.169.254', 'papara.approovr.io', 'https://localhost:3000'] 

MEDIA_ROOT = "var/www/planyourmeals_api/"

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')