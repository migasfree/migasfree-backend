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

from datetime import timedelta

from celery.schedules import crontab

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = 'Europe/Madrid'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

CELERY_IMPORTS = (
    'migasfree.stats.tasks',
    'migasfree.core.tasks',
    'migasfree.core.pms.tasks',
    'migasfree.client.tasks',
    'migasfree.hardware.tasks',
)
CELERY_BEAT_SCHEDULE = {
    'alerts': {
        'task': 'migasfree.stats.tasks.alerts',
        'schedule': timedelta(seconds=10),
        'options': {'expires': 8},
    },
    'computers_deployments': {
        'task': 'migasfree.stats.tasks.computers_deployments',
        'schedule': crontab(hour=0, minute=1),
    },
    'update_deployment_start_date': {
        'task': 'migasfree.core.tasks.update_deployment_start_date',
        'schedule': crontab(hour=0, minute=0),
    },
    'remove_orphan_files_from_external_deployments': {
        'task': 'migasfree.core.tasks.remove_orphan_files_from_external_deployments',
        'schedule': crontab(hour=1, minute=0, day_of_week=6),  # at Sunday
    },
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(REDIS_HOST, REDIS_PORT)],
        },
    }
}

# django-redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': CELERY_BROKER_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    }
}
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
