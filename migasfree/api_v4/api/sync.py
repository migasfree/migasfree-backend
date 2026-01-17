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

"""Core synchronization functions - get_properties and upload_computer_info."""

import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from ...app_catalog.models import Policy
from ...client.messages import add_computer_message, remove_computer_messages
from ...client.models import FaultDefinition, Synchronization, User
from ...client.views.safe import is_computer_changed
from ...core.models import (
    Attribute,
    AttributeSet,
    BasicAttribute,
    Deployment,
    Domain,
    Platform,
    Project,
    Property,
)
from ...utils import get_client_ip, remove_duplicates_preserving_order, replace_keys, to_list
from .. import errmfs
from .helpers import add_notification_platform, add_notification_project, return_message

logger = logging.getLogger('migasfree')


def get_properties(request, name, uuid, computer, data):
    """
    First call of client requesting to server what it must do.

    Returns enabled client properties for the computer to evaluate.
    The client will eval the code and upload results via upload_computer_info.
    """
    return return_message(
        'get_properties',
        {
            'properties': replace_keys(
                Property.enabled_client_properties(computer.get_all_attributes()),
                {'prefix': 'name', 'language': 'language', 'code': 'code'},
            )
        },
    )


def _auto_register_platform(platform_name, computer):
    """Auto-register platform if MIGASFREE_AUTOREGISTER is enabled."""
    if Platform.objects.filter(name=platform_name).exists():
        return None

    if not settings.MIGASFREE_AUTOREGISTER:
        return errmfs.error(errmfs.CAN_NOT_REGISTER_COMPUTER)

    platform = Platform.objects.create(platform_name)
    add_notification_platform(platform, computer)
    return None


def _auto_register_project(project_name, platform_name, pms_name, computer):
    """Auto-register project if MIGASFREE_AUTOREGISTER is enabled."""
    if Project.objects.filter(name=project_name).exists():
        return None, None

    if not settings.MIGASFREE_AUTOREGISTER:
        return errmfs.error(errmfs.CAN_NOT_REGISTER_COMPUTER), None

    platform = Platform.objects.get(name=platform_name)
    project = Project.objects.create(
        name=project_name,
        pms=pms_name,
        architecture='amd64',
        platform=platform,
        auto_register_computers=settings.MIGASFREE_AUTOREGISTER,
    )
    add_notification_project(project, pms_name, computer)
    return None, project


def _process_attributes(computer, client_attributes, user):
    """Process and add all sync attributes for the computer."""
    attributes_to_add = []

    # Basic attributes
    attributes_to_add.extend(
        BasicAttribute.process(
            id=computer.id,
            ip_address=computer.ip_address,
            project=computer.project.name,
            platform=computer.project.platform.name,
            user=user.name,
            description=computer.get_cid_description(),
        )
    )

    # Prefetch all client properties in one query
    client_property_map = {
        prop.prefix: prop for prop in Property.objects.filter(prefix__in=client_attributes.keys(), sort='client')
    }

    # Client attributes
    for prefix, value in client_attributes.items():
        client_property = client_property_map.get(prefix)
        if client_property:
            attributes_to_add.extend(Attribute.process_kind_property(client_property, value))

    # Batch add basic and client attributes
    computer.sync_attributes.add(*attributes_to_add)

    # Cache get_all_attributes
    all_attributes = computer.get_all_attributes()

    # Domain attribute
    computer.sync_attributes.add(*Domain.process(all_attributes))

    # Tags (server attributes)
    tags_attrs = []
    for tag in computer.tags.select_related('property_att').filter(property_att__enabled=True):
        tags_attrs.extend(Attribute.process_kind_property(tag.property_att, tag.value))
    if tags_attrs:
        computer.sync_attributes.add(*tags_attrs)

    # AttributeSets
    computer.sync_attributes.add(*AttributeSet.process(all_attributes))

    # Return refreshed attributes
    return computer.get_all_attributes()


def _build_sync_response(computer, all_attributes):
    """Build the synchronization response data."""
    # Fault definitions
    fault_definitions = [
        {'language': item.get_language_display(), 'name': item.name, 'code': item.code}
        for item in FaultDefinition.enabled_for_attributes(all_attributes)
    ]

    # Deployments and packages
    lst_pkg_to_remove = []
    lst_pkg_to_install = []

    deploys = Deployment.available_deployments(computer, all_attributes)
    lst_deploys = [{'name': dep.name, 'source_template': dep.source_template()} for dep in deploys]

    for dep in deploys:
        if dep.packages_to_remove:
            lst_pkg_to_remove.extend(pkg for pkg in to_list(dep.packages_to_remove) if pkg)
        if dep.packages_to_install:
            lst_pkg_to_install.extend(pkg for pkg in to_list(dep.packages_to_install) if pkg)

    # Policies
    policy_pkg_to_install, policy_pkg_to_remove = Policy.get_packages(computer)
    lst_pkg_to_install.extend(x['package'] for x in policy_pkg_to_install)
    lst_pkg_to_remove.extend(x['package'] for x in policy_pkg_to_remove)

    # Devices
    logical_devices = [device.as_dict(computer.project) for device in computer.logical_devices(all_attributes)]
    default_logical_device = computer.default_logical_device.id if computer.default_logical_device else 0

    # Hardware capture decision
    capture_hardware = True
    if computer.last_hardware_capture:
        capture_hardware = datetime.now() > (
            computer.last_hardware_capture.replace(tzinfo=None) + timedelta(days=settings.MIGASFREE_HW_PERIOD)
        )

    return {
        'faultsdef': fault_definitions,
        'repositories': lst_deploys,
        'packages': {
            'remove': remove_duplicates_preserving_order(lst_pkg_to_remove),
            'install': remove_duplicates_preserving_order(lst_pkg_to_install),
        },
        'devices': {
            'logical': logical_devices,
            'default': default_logical_device,
        },
        'base': False,  # computerbase and base has been removed
        'hardware_capture': capture_hardware,
    }


def upload_computer_info(request, name, uuid, computer, data):
    """
    Process the computer info request and return sync configuration.

    This is the main synchronization endpoint that processes client attributes
    and returns fault definitions, repositories, packages, and devices.
    """
    cmd = 'upload_computer_info'

    computer_info = data.get(cmd, {}).get('computer', {})
    platform_name = computer_info.get('platform', 'unknown')
    project_name = computer_info.get('version', computer_info.get('project', 'unknown'))
    pms_name = computer_info.get('pms', 'apt')
    fqdn = computer_info.get('fqdn')

    # Normalize PMS name in v5
    if pms_name.startswith('apt'):
        pms_name = 'apt'

    # Auto register platform
    error = _auto_register_platform(platform_name, computer)
    if error:
        return return_message(cmd, error)

    # Auto register project
    error, _ = _auto_register_project(project_name, platform_name, pms_name, computer)
    if error:
        return return_message(cmd, error)

    try:
        client_attributes = data.get(cmd, {}).get('attributes', {})
        ip_address = computer_info.get('ip', '')
        forwarded_ip_address = get_client_ip(request)

        # Get project with platform pre-loaded
        project = Project.objects.select_related('platform').get(name=project_name)

        # Check for computer changes and update identification
        is_computer_changed(computer, name, project, ip_address, uuid)
        if computer:
            computer.update_identification(name, fqdn, project, uuid, ip_address, forwarded_ip_address)

        # Get or create user
        user_fullname = computer_info.get('user_fullname', '')
        user, _ = User.objects.get_or_create(name=computer_info.get('user'), defaults={'fullname': user_fullname})
        user.update_fullname(user_fullname)

        computer.update_sync_user(user)
        computer.sync_attributes.clear()

        # Process all attributes
        all_attributes = _process_attributes(computer, client_attributes, user)

        # Build and return response
        response_data = _build_sync_response(computer, all_attributes)
        return return_message(cmd, response_data)

    except ObjectDoesNotExist as e:
        logger.error('Object not found during sync: %s', e)
        return return_message(cmd, errmfs.error(errmfs.GENERIC))


def upload_computer_message(request, name, uuid, computer, data):
    """Update or clear computer synchronization message."""
    cmd = 'upload_computer_message'

    if not computer:
        return return_message(cmd, errmfs.error(errmfs.COMPUTER_NOT_FOUND))

    message = data.get(cmd, '')

    if message == '':
        remove_computer_messages(computer.id)
        Synchronization.objects.create(computer, consumer='migasfree_4.x', start_date=computer.sync_start_date)
    else:
        add_computer_message(computer, message)

    return return_message(cmd, errmfs.ok())
