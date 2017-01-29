"""
Django settings for taikonetwork project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'salesforce',
    'datahandler',
    'home',
    'map',
    'graph',
    'metrics',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'taikonetwork.urls'

WSGI_APPLICATION = 'taikonetwork.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases
DATABASE_ROUTERS = ['salesforce.router.ModelRouter']
SALESFORCE_QUERY_TIMEOUT = 60

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    },
    'salesforce': {
        'ENGINE': 'salesforce.backend',
        'USER': '',
        'CONSUMER_KEY': '',
        'CONSUMER_SECRET': '',
        'PASSWORD': '',
        'HOST': '',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'static')
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)


# Templates
TEMPLATE_DIRS = (os.path.join(BASE_DIR, 'templates'),)


# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s (%(module)s:%(lineno)s) %(message)s'
        },
        'simple': {
            'format': '[%(levelname)s] %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/webapps/taiko_django/logs/datahandler.log',
            'formatter': 'verbose',
        },
        'sql': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/webapps/taiko_django/logs/datahandler.sql.log',
            'formatter': 'verbose',
        },
        'neo4j': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/webapps/taiko_django/logs/datahandler.neo4j.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'datahandler': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'datahandler.sql_updater': {
            'handlers': ['sql', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'datahandler.neo4j_updater': {
            'handlers': ['neo4j', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'test': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propogate': False,
        },
    },
}


# Override sensitive settings information.
try:
    from taikonetwork.local_settings import *
except ImportError:
    pass
