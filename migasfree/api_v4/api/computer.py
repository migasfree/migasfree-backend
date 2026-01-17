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

"""Computer lookup and registration functions."""

import logging

from django.conf import settings
from django.contrib import auth
from django.core.exceptions import ObjectDoesNotExist

from ...client.models import Computer
from ...client.views.safe import is_computer_changed
from ...core.models import Platform, Project
from ...utils import get_client_ip, uuid_change_format
from .. import errmfs
from ..secure import get_keys_to_client
from .helpers import add_notification_platform, add_notification_project, return_message

logger = logging.getLogger('migasfree')


def _find_by_uuid(uuid):
    """Try to find computer by UUID (standard and endian-swapped formats)."""
    try:
        return Computer.objects.get(uuid=uuid)
    except Computer.DoesNotExist:
        pass

    try:
        return Computer.objects.get(uuid=uuid_change_format(uuid))
    except Computer.DoesNotExist:
        pass

    return None


def _find_by_mac_address(uuid):
    """Try to find computer by MAC address embedded in UUID."""
    if uuid[0:8] != '0' * 8:
        return None

    computers = Computer.objects.filter(mac_address__icontains=uuid[-12:])
    if computers.count() == 1:
        return computers.first()

    return None


def _find_by_name_legacy(name, uuid):
    """
    DEPRECATED: Find computer by name for client <= 2 compatibility.
    """
    is_uuid_format = len(uuid.split('-')) == 5

    if is_uuid_format:
        # Client >= 3: try to find by name as uuid
        try:
            return Computer.objects.get(uuid=name)
        except Computer.DoesNotExist:
            return None

    # Client <= 2: search by name
    try:
        return Computer.objects.get(name=name, uuid=name)
    except Computer.DoesNotExist:
        pass

    try:
        return Computer.objects.get(name=name)
    except (Computer.DoesNotExist, Computer.MultipleObjectsReturned):
        pass

    return None


def get_computer(name, uuid):
    """
    Find and return a computer by various identifiers.

    Search order:
    1. By UUID (exact match)
    2. By UUID (endian format swapped)
    3. By MAC address (if UUID starts with zeros)
    4. Legacy: by name (for client <= 2 compatibility)

    Returns Computer object or None if not found.
    """
    logger.debug('Looking up computer - name: %s, uuid: %s', name, uuid)

    # Try UUID-based lookups
    computer = _find_by_uuid(uuid)
    if computer:
        logger.debug('Computer found by UUID')
        return computer

    # Try MAC address
    computer = _find_by_mac_address(uuid)
    if computer:
        logger.debug('Computer found by MAC address (in UUID format)')
        return computer

    # Legacy fallback for old clients
    computer = _find_by_name_legacy(name, uuid)
    if computer:
        logger.debug('Computer found by name (legacy compatibility mode)')
        return computer

    logger.debug('Computer not found')
    return None


def _can_register_platform(user):
    """Check if platform can be auto-registered or user has permission."""
    return settings.MIGASFREE_AUTOREGISTER or (user and user.has_perm('core.add_platform'))


def _can_register_project(user):
    """Check if project can be auto-registered or user has permission."""
    return settings.MIGASFREE_AUTOREGISTER or (user and user.has_perm('core.add_project'))


def _can_register_computer(user, project):
    """Check if computer can be registered based on project settings and user permissions."""
    if project.auto_register_computers:
        return True
    return user and user.has_perm('client.add_computer') and user.has_perm('client.change_computer')


def register_computer(request, name, uuid, computer, data):
    """
    Register or update a computer in the system.

    Handles auto-registration of platform and project if enabled,
    validates user permissions, and returns client keys on success.
    """
    cmd = 'register_computer'

    user = auth.authenticate(username=data.get('username'), password=data.get('password'))

    platform_name = data.get('platform', 'unknown')
    project_name = data.get('version', data.get('project', 'unknown'))
    pms_name = data.get('pms', 'apt')
    fqdn = data.get('fqdn')
    ip_address = data.get('ip', '')

    # Normalize PMS name in v5
    if pms_name.startswith('apt'):
        pms_name = 'apt'

    # Auto-register platform if needed
    platform_created = False
    if not Platform.objects.filter(name=platform_name).exists():
        if not _can_register_platform(user):
            return return_message(cmd, errmfs.error(errmfs.CAN_NOT_REGISTER_COMPUTER))
        Platform.objects.create(platform_name)
        platform_created = True

    # Auto-register project if needed
    project_created = False
    if not Project.objects.filter(name=project_name).exists():
        if not _can_register_project(user):
            return return_message(cmd, errmfs.error(errmfs.CAN_NOT_REGISTER_COMPUTER))

        platform = Platform.objects.get(name=platform_name)
        Project.objects.create(
            name=project_name,
            pms=pms_name,
            architecture='amd64',
            platform=platform,
            auto_register_computers=settings.MIGASFREE_AUTOREGISTER,
        )
        project_created = True

    try:
        # Get project with platform prefetched
        project = Project.objects.select_related('platform').get(name=project_name)

        # Check computer registration permissions
        if not _can_register_computer(user, project):
            return return_message(cmd, errmfs.error(errmfs.CAN_NOT_REGISTER_COMPUTER))

        # Update or create computer
        is_computer_changed(computer, name, project, ip_address, uuid)
        if computer:
            computer.update_identification(name, fqdn, project, uuid, ip_address, get_client_ip(request))

        # Send notifications for new platform/project
        if platform_created:
            add_notification_platform(project.platform, computer)
        if project_created:
            add_notification_project(project, pms_name, computer)

        # Add computer to user's domain preference
        if user and hasattr(user, 'userprofile') and user.userprofile.domain_preference:
            user.userprofile.domain_preference.included_attributes.add(computer.get_cid_attribute())

        return return_message(cmd, get_keys_to_client(project_name))

    except ObjectDoesNotExist as e:
        logger.error('Registration failed - object not found: %s', e)
        return return_message(cmd, errmfs.error(errmfs.USER_DOES_NOT_HAVE_PERMISSION))
