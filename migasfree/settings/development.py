# Copyright (c) 2015-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2026 Alberto Gacías <alberto@migasfree.org>
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

from .base import *
from .celery import (  # noqa: F401
    CACHES,
    CELERY_ACCEPT_CONTENT,
    CELERY_BEAT_SCHEDULE,
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP,
    CELERY_BROKER_URL,
    CELERY_ENABLE_UTC,
    CELERY_IMPORTS,
    CELERY_RESULT_BACKEND,
    CELERY_RESULT_SERIALIZER,
    CELERY_TASK_DEFAULT_QUEUE,
    CELERY_TASK_SERIALIZER,
    CELERY_TASK_SOFT_TIME_LIMIT,
    CELERY_TASK_TIME_LIMIT,
    CELERY_TIMEZONE,
    CHANNEL_LAYERS,
    SESSION_CACHE_ALIAS,
    SESSION_ENGINE,
)
from .functions import secret_key
from .migasfree import (  # noqa: F401
    DAILY_RANGE,
    HOURLY_RANGE,
    MAX_FILE_SIZE,
    MIGASFREE_APP_DIR,
    MIGASFREE_AUTOREGISTER,
    MIGASFREE_COMPUTER_SEARCH_FIELDS,
    MIGASFREE_DEFAULT_COMPUTER_STATUS,
    MIGASFREE_EXTERNAL_ACTIONS,
    MIGASFREE_EXTERNAL_TRAILING_PATH,
    MIGASFREE_FQDN,
    MIGASFREE_HELP_DESK,
    MIGASFREE_HW_PERIOD,
    MIGASFREE_INVALID_UUID,
    MIGASFREE_NOTIFY_CHANGE_IP,
    MIGASFREE_NOTIFY_CHANGE_NAME,
    MIGASFREE_NOTIFY_CHANGE_UUID,
    MIGASFREE_NOTIFY_NEW_COMPUTER,
    MIGASFREE_ORGANIZATION,
    MIGASFREE_PACKAGER_PRI_KEY,
    MIGASFREE_PACKAGER_PUB_KEY,
    MIGASFREE_PRIVATE_KEY,
    MIGASFREE_PROGRAMMING_LANGUAGES,
    MIGASFREE_PROJECT_DIR,
    MIGASFREE_PUBLIC_KEY,
    MIGASFREE_REPOSITORY_TRAILING_PATH,
    MIGASFREE_SECONDS_MESSAGE_ALERT,
    MIGASFREE_SECRET_DIR,
    MIGASFREE_SETTINGS_OVERRIDE,
    MIGASFREE_STORE_TRAILING_PATH,
    MIGASFREE_TMP_DIR,
    MIGASFREE_TMP_TRAILING_PATH,
    MONTHLY_RANGE,
)

# development environment
DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG
LOGGING['loggers']['migasfree']['level'] = 'DEBUG'
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['handlers']['file']['level'] = 'DEBUG'
LOGGING['loggers']['django.db.backends'] = {
    'level': 'DEBUG',
    'handlers': ['console'],
}
LOGGING['loggers']['celery'] = {
    'level': 'DEBUG',
    'handlers': ['console'],
    # 'propagate': False,
}

MIGASFREE_PUBLIC_DIR = os.path.join(MIGASFREE_PROJECT_DIR, 'pub')
MIGASFREE_KEYS_DIR = os.path.join(MIGASFREE_APP_DIR, 'keys')

MIGASFREE_FQDN = 'localhost:2345'  # noqa: F811

MIGASFREE_COMPUTER_SEARCH_FIELDS = ('name', 'ip_address')  # noqa: F811

SECRET_KEY = secret_key(MIGASFREE_KEYS_DIR)

STATIC_ROOT = os.path.join(MIGASFREE_APP_DIR, 'static')
MEDIA_ROOT = MIGASFREE_PUBLIC_DIR

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'migasfree_backend',
        'USER': 'migasfree_backend',
        'PASSWORD': 'migasfree_backend',
        'HOST': 'localhost',
        'PORT': '',
    }
}

if os.environ.get('GITHUB_WORKFLOW'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'github_actions',
            'USER': 'postgres',
            'PASSWORD': 'postgres',
            'HOST': '127.0.0.1',
            'PORT': '5432',
        }
    }

# python manage.py graph_models -a -o myapp_models.png
INSTALLED_APPS += (
    'debug_toolbar',
    'django_extensions',
    'silk',
)
INTERNAL_IPS = ('127.0.0.1',)

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'silk.middleware.SilkyMiddleware',
]

CORS_ORIGIN_ALLOW_ALL = True

ALLOWED_HOSTS = ['*']
