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

import importlib.util  # noqa: I001
from pathlib import Path

from .base import *
from .functions import secret_key
from .migasfree import *
from .celery import *

# production environment
DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

ALLOWED_HOSTS = ['*']

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
