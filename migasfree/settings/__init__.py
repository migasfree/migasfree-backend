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

django_settings = os.environ.get('DJANGO_SETTINGS_MODULE', '')

# Map of allowed settings modules for security
# Only these explicit modules can be loaded
_ALLOWED_SETTINGS = {
    'migasfree.settings.development': 'development',
    'migasfree.settings.production': 'production',
}

_settings_name = _ALLOWED_SETTINGS.get(django_settings)

if _settings_name == 'development':
    from .development import *  # noqa: F403
else:
    # Default to production for safety (including empty or invalid values)
    from .production import *  # noqa: F403

del _settings_name, _ALLOWED_SETTINGS
