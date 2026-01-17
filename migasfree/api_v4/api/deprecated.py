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

"""Deprecated endpoints kept for backward compatibility."""

import logging

from .. import errmfs
from .helpers import return_message

logger = logging.getLogger('migasfree')


def upload_devices_changes(request, name, uuid, computer, data):
    """DEPRECATED endpoint for migasfree-client >= 4.13"""
    logger.debug('upload_devices_changes data: %s', data)
    cmd = 'upload_devices_changes'

    return return_message(cmd, errmfs.ok())
