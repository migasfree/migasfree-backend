# -*- coding: utf-8 -*-

# Copyright (c) 2015 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015 Alberto Gacías <alberto@migasfree.org>
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

from .migasfree import *
from .base import *
from .celery import *
from .functions import secret_key

# development environment
DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

MIGASFREE_DB_DIR = os.path.dirname(MIGASFREE_PROJECT_DIR)
MIGASFREE_PUBLIC_DIR = os.path.join(MIGASFREE_PROJECT_DIR, 'pub')
MIGASFREE_KEYS_PATH = os.path.join(MIGASFREE_APP_DIR, 'keys')

MIGASFREE_NOTIFY_NEW_COMPUTER = True

SECRET_KEY = secret_key(MIGASFREE_KEYS_PATH)

STATIC_ROOT = os.path.join(MIGASFREE_APP_DIR, 'static')
MEDIA_ROOT = MIGASFREE_PUBLIC_DIR

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(MIGASFREE_DB_DIR, 'migasfree-backend.db'),
    }
}

# python manage.py graph_models -a -o myapp_models.png
INSTALLED_APPS = ('debug_toolbar', 'django_extensions') + INSTALLED_APPS
INTERNAL_IPS = ("127.0.0.1",)

MIDDLEWARE_CLASSES += ("debug_toolbar.middleware.DebugToolbarMiddleware",)

CORS_ORIGIN_ALLOW_ALL = True
