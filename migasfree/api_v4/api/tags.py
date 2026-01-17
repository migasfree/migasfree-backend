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

"""Computer tags management functions."""

import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from ...core.models import Attribute, Deployment, Domain, ServerAttribute
from ...utils import list_common, list_difference, to_list
from .. import errmfs
from .helpers import return_message

logger = logging.getLogger('migasfree')


def _get_domain_tags(tag):
    """Get all tags from a domain if tag is a domain tag."""
    if tag.property_att.prefix != 'DMN':
        return {}

    domain_tags = {}
    try:
        domain = Domain.objects.get(name=tag.value.split('.')[0])
        for tag_dmn in domain.get_tags():
            domain_tags.setdefault(tag_dmn.property_att.name, []).append(str(tag_dmn))
    except ObjectDoesNotExist:
        logger.warning('Domain not found for tag: %s', tag.value)

    return domain_tags


def _get_deployment_tags(project):
    """Get all server tags from enabled deployments for a project."""
    tags = {}
    deployments = Deployment.objects.filter(project=project, enabled=True).prefetch_related(
        'included_attributes__property_att'
    )

    for deploy in deployments:
        for tag in deploy.included_attributes.filter(property_att__sort='server', property_att__enabled=True):
            tags.setdefault(tag.property_att.name, []).append(str(tag))

    return tags


def _get_accessible_domain_tags(sync_attributes):
    """Get tags from domains accessible by the computer's sync attributes."""
    tags = {}
    domains = (
        Domain.objects.filter(Q(included_attributes__in=sync_attributes) & ~Q(excluded_attributes__in=sync_attributes))
        .prefetch_related('tags__property_att')
        .distinct()
    )

    for domain in domains:
        for tag in domain.tags.all():
            tags.setdefault(tag.property_att.name, []).append(str(tag))

    return tags


def get_computer_tags(request, name, uuid, computer, data):
    """
    Get available and selected tags for a computer.

    Returns a dict with 'available' (tags the computer can select)
    and 'selected' (tags currently assigned to the computer).
    """
    cmd = 'get_computer_tags'

    # Build selected tags list and collect domain tags
    available_tags = {}
    selected_tags = []

    for tag in computer.tags.select_related('property_att').all():
        selected_tags.append(str(tag))
        # If tag is a domain, include all domain's tags
        available_tags.update(_get_domain_tags(tag))

    # Add deployment tags
    deployment_tags = _get_deployment_tags(computer.project)
    for name, values in deployment_tags.items():
        available_tags.setdefault(name, []).extend(values)

    # Add accessible domain tags
    domain_tags = _get_accessible_domain_tags(computer.sync_attributes.all())
    for name, values in domain_tags.items():
        available_tags.setdefault(name, []).extend(values)

    response = errmfs.ok()
    response['available'] = available_tags
    response['selected'] = selected_tags

    return return_message(cmd, response)


def _parse_tags(tags_data):
    """Parse tag strings and return ServerAttribute objects and IDs."""
    tags_objects = []
    tags_ids = []

    for tag in tags_data:
        parts = tag.split('-', 1)
        if len(parts) > 1:
            prefix, value = parts
            attribute = ServerAttribute.objects.get(property_att__prefix=prefix, value=value)
            tags_objects.append(attribute)
            tags_ids.append(attribute.id)

    return tags_objects, tags_ids


def _calculate_package_changes(computer, old_tags_id, new_tags_id, common_tags_id):
    """Calculate package changes based on tag differences."""
    pkg_remove = []
    pkg_install = []
    pkg_preinstall = []

    # Old deployments - INVERSE the operations
    for deploy in Deployment.available_deployments(computer, old_tags_id):
        pkg_remove.extend(
            to_list(
                f'{deploy.packages_to_install} {deploy.default_included_packages} {deploy.default_preincluded_packages}'
            )
        )
        pkg_install.extend(to_list(f'{deploy.packages_to_remove} {deploy.default_excluded_packages}'))

    # New deployments
    for deploy in Deployment.available_deployments(computer, new_tags_id + common_tags_id):
        pkg_remove.extend(to_list(f'{deploy.packages_to_remove} {deploy.default_excluded_packages}'))
        pkg_install.extend(to_list(f'{deploy.packages_to_install} {deploy.default_included_packages}'))
        pkg_preinstall.extend(to_list(deploy.default_preincluded_packages))

    return pkg_remove, pkg_install, pkg_preinstall


def set_computer_tags(request, name, uuid, computer, data):
    """
    Set computer tags and calculate resulting package changes.

    Compares old and new tags to determine which packages need to be
    installed, removed, or preinstalled based on deployment configurations.
    """
    cmd = 'set_computer_tags'

    # "All Systems" attribute is always ID 1
    all_systems_id = Attribute.objects.get(pk=1).id

    try:
        # Parse requested tags
        tags_objects, tags_ids = _parse_tags(data['set_computer_tags']['tags'])
        tags_ids.append(all_systems_id)

        # Get current computer tags
        current_tags_ids = list(computer.tags.values_list('id', flat=True))
        current_tags_ids.append(all_systems_id)

        # Calculate tag differences
        old_tags_id = list_difference(current_tags_ids, tags_ids)
        new_tags_id = list_difference(tags_ids, current_tags_ids)
        common_tags_id = list_common(current_tags_ids, tags_ids)

        # Calculate package changes
        pkg_remove, pkg_install, pkg_preinstall = _calculate_package_changes(
            computer, old_tags_id, new_tags_id, common_tags_id
        )

        # Apply new tags
        computer.tags.set(tags_objects)

        response = errmfs.ok()
        response['packages'] = {
            'preinstall': pkg_preinstall,
            'install': pkg_install,
            'remove': pkg_remove,
        }

        return return_message(cmd, response)

    except ObjectDoesNotExist as e:
        logger.error('Tag not found: %s', e)
        return return_message(cmd, errmfs.error(errmfs.GENERIC))
