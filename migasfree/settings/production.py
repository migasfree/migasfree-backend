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

import importlib.util
import os
from pathlib import Path

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

# production environment
DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost').split(',')

MIGASFREE_PUBLIC_DIR = '/var/lib/migasfree-backend/public'
MIGASFREE_KEYS_DIR = '/var/lib/migasfree-backend/keys'

STATIC_ROOT = '/var/lib/migasfree-backend/static'
MEDIA_ROOT = MIGASFREE_PUBLIC_DIR

SECRET_KEY = secret_key(MIGASFREE_KEYS_DIR)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'migasfree_backend',
        'USER': 'migasfree_backend',
        'PASSWORD': 'migasfree_backend',
        'HOST': '',
        'PORT': '',
    }
}

# Load settings overrides from external Python file
_overrides_file = Path(MIGASFREE_SETTINGS_OVERRIDE)
if _overrides_file.exists():
    _spec = importlib.util.spec_from_file_location('settings_override', _overrides_file)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)

    # Apply only uppercase settings from the override module
    for _key in dir(_mod):
        if _key.isupper():
            globals()[_key] = getattr(_mod, _key)

    del _spec, _mod, _key

del _overrides_file
