"""
Django settings for base project.

Generated by 'django-admin startproject' using Django 1.11.12.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import dj_database_url
from conversion import convert_bool

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'g!u%+x7#3(9@ix=o&377e2-!4=iqke-rnbkd*2s$9zf$orfm2v')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = convert_bool(os.environ.get('DEBUG', '0'))

ALLOWED_HOSTS = ['*']

# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

SUPPORT_APPS = ['jet', 'rest_framework', 'django_extensions', 'debug_toolbar', 'nested_admin', 'audit_trail']
CUSTOM_APPS = ['custom_apps.invoices', 'custom_apps.utils', 'custom_apps.data_ingestion',]

INSTALLED_APPS = CUSTOM_APPS + SUPPORT_APPS + DJANGO_APPS

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'custom_apps.utils.middleware.PermissionsErrorMiddleware',
]

ROOT_URLCONF = 'base.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates/')],
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

WSGI_APPLICATION = 'base.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

_sqlite = os.path.join(BASE_DIR, 'db.sqlite3')
_db_conf = dj_database_url.config(default='sqlite:///%s' % _sqlite)
if 'postgres' in _db_conf['ENGINE'].lower():
    import psycopg2.extensions

    _options_conf = _db_conf.get('OPTIONS', {})
    _options_conf.update({'isolation_level': psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ})
    _db_conf['OPTIONS'] = _options_conf
DATABASES = {
    'default': _db_conf
}
ATOMIC_REQUESTS = True

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'collected_static')
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
)

STATICFILES_DIRS = ['static/']

LOGGING_CONFIG = None

LOGGING_DEFAULT = {
    'handlers': ['console'],
    'level': 'INFO',
    'propagate': False,
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': LOGGING_DEFAULT,
    'formatters': {
        'json': {
            '()': 'custom_apps.utils.logutils.JSONFormatter',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'request': {
            '()': 'custom_apps.utils.logutils.LoggingFilter',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'filters': ['request'],
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': LOGGING_DEFAULT,
        'django.db.backends': {
            'level': 'INFO'
        }
    }
}

# debug toolbar settings
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_COLLAPSED': True,
    'RESULTS_CACHE_SIZE': 1000,
    'RENDER_PANELS': True,
    'SHOW_TOOLBAR_CALLBACK': 'custom_apps.utils.djdt.callback'
}

# google specific setup
GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', 'AIzaSyAFd7fBl1dVKvfNFxLDFchKbYxeC_QU490')

# email
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY',
                                  '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')
SENDGRID_SANDBOX_MODE_IN_DEBUG = False
DEFAULT_FROM_EMAIL = 'noreply@nobelw.co'

# celery
if 'BROKER_URL' in os.environ:
    CELERY_BROKER_URL = os.environ.get('BROKER_URL')
    CELERY_TASK_ACKS_LATE = True
    CELERY_TASK_REJECT_ON_WORKER_LOSS = True
else:
    CELERY_TASK_ALWAYS_EAGER = True

CELERY_WORKER_HIJACK_ROOT_LOGGER = False

# gcloud
GOOGLE_CLOUD_JSON = os.path.join(BASE_DIR, 'google-cloud.json')
