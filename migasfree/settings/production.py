# -*- coding: utf-8 -*-

# Copyright (c) 2015-2016 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2016 Alberto Gacías <alberto@migasfree.org>
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

from .migasfree import *
from .base import *
from .celery import *
from .functions import secret_key

# production environment
DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

ALLOWED_HOSTS = ['*']

MIGASFREE_PUBLIC_DIR = '/var/lib/migasfree-backend/public'
MIGASFREE_KEYS_PATH = '/var/lib/migasfree-backend/keys'

SECRET_KEY = secret_key(MIGASFREE_KEYS_PATH)

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

try:
    execfile(MIGASFREE_SETTINGS_OVERRIDE, globals(), locals())
except IOError:
    pass
