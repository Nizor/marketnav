from .settings import *
import os
from decouple import config as decouple_config

#Basic Settings
DEBUG = decouple_config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = decouple_config(
    'ALLOWED_HOSTS',
    default='marketnav.ng,www.marketnav.ng,51.20.107.70,localhost,127.0.0.1',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# Database — Supabase
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': decouple_config('DB_NAME', 'postgres'),
        'USER': decouple_config('DB_USER'),
        'PASSWORD': decouple_config('DB_PASSWORD'),
        'HOST': decouple_config('DB_HOST'),
        'PORT': decouple_config('DB_PORT', '6543'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# S3 for media and static files
# Uncomment if you want to use S3 for media/static files

# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
AWS_STORAGE_BUCKET_NAME = decouple_config('AWS_STORAGE_BUCKET_NAME', '')
AWS_S3_REGION_NAME = decouple_config('AWS_S3_REGION_NAME', 'eu-north-1')
AWS_S3_CUSTOM_DOMAIN = decouple_config('AWS_S3_CUSTOM_DOMAIN', '')
# MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/' if AWS_S3_CUSTOM_DOMAIN else '/media/'
# STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/' if AWS_S3_CUSTOM_DOMAIN else '/static/'


# Security
SECURE_SSL_REDIRECT = decouple_config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = decouple_config('SESSION_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_SECURE = decouple_config('CSRF_COOKIE_SECURE', default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

#Static and Media
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

#CORS
CORS_ALLOW_ALL_ORIGINS = decouple_config('CORS_ALLOW_ALL_ORIGINS', default=False, cast=bool)
CORS_ALLOWED_ORIGINS = decouple_config(
    'CORS_ALLOWED_ORIGINS',
    default='',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]
)
