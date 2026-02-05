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

"""Repository metadata creation functions."""

import logging
import os

from django.core.exceptions import ObjectDoesNotExist

from ...core.models import Deployment, Package, Project
from ...core.pms.tasks import create_repository_metadata
from .. import errmfs
from .helpers import return_message

logger = logging.getLogger('migasfree')


def create_repositories_package(package_name, project_name):
    """
    Trigger repository metadata creation for all deployments
    containing the specified package.
    """
    try:
        project = Project.objects.get(name=project_name)
        package = Package.objects.get(name=package_name, project=project)

        # Prefetch related PMS to avoid N+1 queries
        deployments = Deployment.objects.filter(available_packages__id=package.id).select_related('project')

        for deploy in deployments:
            pms_name = deploy.pms().name
            create_repository_metadata.apply_async(
                queue=f'pms-{pms_name}', kwargs={'payload': deploy.get_repository_metadata_payload()}
            )
            logger.debug('Queued repository metadata creation for deployment %s', deploy.name)
    except ObjectDoesNotExist:
        logger.warning('Package %s not found in project %s', package_name, project_name)


def create_repositories_of_packageset(request, name, uuid, computer, data):
    cmd = 'create_repositories_of_packageset'
    project_name = data.get('version', data.get('project'))

    try:
        package_name = os.path.basename(data['packageset'])
        create_repositories_package(package_name, project_name)
        return return_message(cmd, errmfs.ok())
    except KeyError as e:
        logger.error('Missing required field in request: %s', e)
        return return_message(cmd, errmfs.error(errmfs.GENERIC))
