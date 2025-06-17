# -*- coding: utf-8 -*-

# Copyright (c) 2015-2025 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2025 Alberto Gacías <alberto@migasfree.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import sys

import django
import django.conf.global_settings as DEFAULT_SETTINGS

from corsheaders.defaults import default_headers

from .migasfree import BASE_DIR, MIGASFREE_TMP_DIR
from .. import __contact__

if django.VERSION < (4, 2, 0, 'final'):
    print('Migasfree requires Django 4.2.0 at least. Please, update it.')
    sys.exit(1)

ADMINS = (
    ('Your name', 'your_name@example.com'),
)

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Madrid'

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

FIRST_DAY_OF_WEEK = 1
DATE_FORMAT = 'Y-m-d'
DATETIME_FORMAT = 'Y-m-d H:i:s'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'es'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
)

STATIC_URL = '/static/'
MEDIA_URL = '/pub/'

FILE_UPLOAD_TEMP_DIR = MIGASFREE_TMP_DIR

LOGIN_REDIRECT_URL = '/'

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'i18n'),
)

ADMIN_SITE_ROOT_URL = '/admin/'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

DEFAULT_CHARSET = 'utf-8'

ROOT_URLCONF = 'migasfree.urls'

ASGI_APPLICATION = 'migasfree.asgi.application'
WSGI_APPLICATION = 'migasfree.wsgi.application'

# Django 3.2: The app label is not a valid Python identifier (hyphens in name)
sys.modules['django_partial_content'] = __import__('django-partial-content')

INSTALLED_APPS = (
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.humanize',
    'django.contrib.admindocs',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_partial_content',
    'graphene_django',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'dj_rest_auth',
    'django_filters',
    'corsheaders',
    'djoser',
    'import_export',
    'markdownx',
    'channels',
    'migasfree.core',
    'migasfree.app_catalog',
    'migasfree.client',
    'migasfree.stats',
    'migasfree.hardware',
    'migasfree.device',
    'migasfree.api_v4',
)

DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 100  # 100 MB

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
        'rest_framework.filters.SearchFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'migasfree.paginations.DefaultPagination',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/second',
        'user': '1000/second',
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Migasfree REST API',
    'VERSION': 'v1',
    'SERVE_INCLUDE_SCHEMA': False,
    'SERVE_PUBLIC': True,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SERVE_AUTHENTICATION': None,
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,
        'displayOperationId': False,
    },
    'REDOC_DIST': 'SIDECAR',
    'CONTACT': {'email': __contact__},
    'LICENSE': {'name': 'GPLv3'},
}

REST_AUTH = {
    'USER_DETAILS_SERIALIZER': 'migasfree.core.serializers.UserProfileSerializer',
}

GRAPHENE = {
    'SCHEMA': 'migasfree.schema.schema'
}

CORS_ALLOW_HEADERS = list(default_headers) + [
    'accept-language',
]

# http://docs.python.org/2/howto/logging-cookbook.html
# http://docs.python.org/2/library/logging.html#logrecord-attributes
LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s - %(levelname)s - %(process)d - %(module)s '
                      '- %(lineno)d - %(funcName)s - %(message)s',
        },
        'simple': {
            'format': '%(asctime)s - %(levelname)s - %(filename)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(MIGASFREE_TMP_DIR, 'migasfree-backend.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
        },
        'celery': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(MIGASFREE_TMP_DIR, 'migasfree-celery.log'),
            'formatter': 'simple',
            'maxBytes': 1024 * 1024 * 100,  # 100 MB
        },
    },
    'loggers': {
        'migasfree': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
        },
        'celery': {
            'handlers': ['celery', 'console'],
            'level': 'DEBUG',
        },
        'daphne': {
            'handlers': ['console'],
        },
    },
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.request',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': False,
        }
    }
]

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

SWAGGER_SETTINGS = {
    'LOGIN_URL': '/rest-auth/login/',
    'LOGOUT_URL': '/rest-auth/logout/'
}

SESSION_COOKIE_NAME = 'migasfree_backend'
# CSRF_COOKIE_NAME = 'csrftoken_migasfree_backend'  # issue with markdownx component :_(
