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

from .migasfree import *
from .base import *
from .functions import secret_key

# production environment
TEMPLATE_DEBUG = DEBUG = False

ALLOWED_HOSTS = ['*']

MIGASFREE_DB_DIR = '/usr/share/migasfree-server'
MIGASFREE_PUBLIC_DIR = '/var/migasfree/pub'
MIGASFREE_KEYS_PATH = os.path.join(MIGASFREE_DB_DIR, 'keys')

SECRET_KEY = secret_key(MIGASFREE_KEYS_PATH)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'migasfree',
        'USER': 'migasfree',
        'PASSWORD': 'migasfree',
        'HOST': '',
        'PORT': '',
    }
}

try:
    execfile('/etc/migasfree-server/settings.py', globals(), locals())
except IOError:
    pass
