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

"""Helper functions used across API v4 modules."""

import contextlib
import logging
import os

from django.utils.translation import gettext as _

from ...client.models import Notification

logger = logging.getLogger('migasfree')


def add_notification_platform(platform, computer):
    """Create a notification when a new platform is auto-registered."""
    Notification.objects.create(_('Platform [%s] registered by computer [%s].') % (platform, computer))
    logger.info('Platform %s auto-registered by computer %s', platform, computer)


def add_notification_project(project, pms, computer):
    """Create a notification when a new project is auto-registered."""
    Notification.objects.create(
        _('Project [%s] with P.M.S. [%s] registered by computer [%s].') % (project, pms, computer)
    )
    logger.info('Project %s (PMS: %s) auto-registered by computer %s', project, pms, computer)


def return_message(cmd, data):
    """
    Format API response in the expected v4 format.

    Args:
        cmd: Command name (e.g., 'get_properties')
        data: Response data (dict or error object)

    Returns:
        Dict with key '{cmd}.return' containing the data
    """
    return {f'{cmd}.return': data}


def save_request_file(archive, target):
    """
    Save an uploaded file to the target path.

    Handles chunked uploads and cleans up temporary files created by Django
    for uploads larger than FILE_UPLOAD_MAX_MEMORY_SIZE.

    Args:
        archive: Django UploadedFile object
        target: Destination file path
    """
    with open(target, 'wb+') as file_handle:
        for chunk in archive.chunks():
            file_handle.write(chunk)

    # Clean up Django's temporary file if it exists
    with contextlib.suppress(OSError, AttributeError):
        temp_path = archive.temporary_file_path()
        os.remove(temp_path)
        logger.debug('Cleaned up temporary upload file: %s', temp_path)
