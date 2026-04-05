from .settings import *
import os

DEBUG = False
ALLOWED_HOSTS = ['marketnav.ng', 'www.marketnav.ng','51.20.107.70', 'localhost','127.0.0.1']

# Database — Supabase
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres.xqrjbkjseuuvxnuqzyqg',
        'PASSWORD': 'A@dT6*UtSGR/!Pu',
        'HOST': 'aws-1-eu-central-1.pooler.supabase.com',
        'PORT': '6543',
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# S3 for media and static files
#DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
#STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
AWS_STORAGE_BUCKET_NAME = 'marketnav-media-prod'
AWS_S3_REGION_NAME = 'eu-north-1'
AWS_S3_CUSTOM_DOMAIN = 'YOUR_CLOUDFRONT_DOMAIN'
#MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
#STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
