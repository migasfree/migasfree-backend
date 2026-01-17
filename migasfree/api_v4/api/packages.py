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

"""Package and package set upload functions."""

import contextlib
import logging
import os

from django.core.exceptions import ObjectDoesNotExist

from ...core.models import Package, PackageSet, Project, Store
from ...core.pms.tasks import package_metadata
from ...utils import save_tempfile
from .. import errmfs
from .helpers import return_message

logger = logging.getLogger('migasfree')


def get_package_data(uploaded_file, project):
    """
    Extract package metadata (name, version, architecture).

    First tries to parse from filename. If that fails, saves the file
    temporarily and uses a Celery task to extract metadata from the
    package contents.

    Args:
        uploaded_file: Django UploadedFile object
        project: Project instance

    Returns:
        Tuple of (name, version, architecture) or (None, None, None)
    """
    name, version, architecture = Package.normalized_name(uploaded_file.name)

    if name:
        return name, version, architecture

    # Fallback: extract metadata from package contents
    package_path = save_tempfile(uploaded_file)
    try:
        response = package_metadata.apply_async(
            kwargs={'pms_name': project.pms, 'package': package_path}, queue=f'pms-{project.pms}'
        ).get()

        if response.get('name'):
            name = response['name']
            version = response['version']
            architecture = response['architecture']
            logger.debug('Extracted package metadata: %s %s %s', name, version, architecture)
    finally:
        os.remove(package_path)

    return name, version, architecture


def _get_or_create_package(uploaded_file, project, store):
    """Get existing package or create a new one."""
    name, version, architecture = get_package_data(uploaded_file, project)

    package = Package.objects.filter(fullname=uploaded_file.name, project=project).first()

    if package:
        package.update_store(store)
        if name and version and architecture:
            package.update_package_data(name, version, architecture)
        logger.debug('Updated existing package: %s', uploaded_file.name)
    else:
        package = Package.objects.create(
            fullname=uploaded_file.name,
            name=name,
            version=version,
            architecture=architecture,
            project=project,
            store=store,
            file_=uploaded_file,
        )
        logger.info('Created new package: %s', uploaded_file.name)

    return package


def upload_server_package(request, name, uuid, computer, data):
    """
    Upload a package to the server.

    Creates or updates a package in the specified store for the project.
    """
    cmd = 'upload_server_package'

    project_name = data.get('version', data.get('project'))

    try:
        project = Project.objects.get(name=project_name)
    except ObjectDoesNotExist:
        logger.error('Project not found: %s', project_name)
        return return_message(cmd, errmfs.error(errmfs.PROJECT_NOT_FOUND))

    store, created = Store.objects.get_or_create(name=data['store'], project=project)
    if created:
        logger.info('Created store: %s for project %s', data['store'], project_name)

    uploaded_file = request.FILES['package']
    _get_or_create_package(uploaded_file, project, store)

    # Save file to disk
    target = Package.path(project.slug, store.slug, uploaded_file.name)
    Package.handle_uploaded_file(uploaded_file, target)

    return return_message(cmd, errmfs.ok())


def upload_server_set(request, name, uuid, computer, data):
    """
    Upload a package as part of a package set.

    Creates or updates the package set, adds the package to it,
    and optionally moves the file to a subdirectory.
    """
    cmd = 'upload_server_set'

    project_name = data.get('version', data.get('project'))
    uploaded_file = request.FILES['package']

    try:
        project = Project.objects.get(name=project_name)
    except ObjectDoesNotExist:
        logger.error('Project not found: %s', project_name)
        return return_message(cmd, errmfs.error(errmfs.PROJECT_NOT_FOUND))

    store, _ = Store.objects.get_or_create(name=data['store'], project=project)

    # Get or create package set
    package_set_name = data['packageset']
    package_set = PackageSet.objects.filter(name=package_set_name, project=project).first()

    if package_set:
        package_set.update_store(store)
    else:
        package_set = PackageSet.objects.create(
            name=package_set_name,
            project=project,
            store=store,
        )
        logger.info('Created package set: %s', package_set_name)

    # Get or create package
    package = _get_or_create_package(uploaded_file, project, store)

    # Save file to disk
    target = Package.path(project.slug, store.slug, uploaded_file.name)
    Package.handle_uploaded_file(uploaded_file, target)

    # Move to subdirectory if path specified
    subpath = data.get('path', '')
    if subpath:
        dst = os.path.join(Store.path(project.slug, store.slug), subpath, uploaded_file.name)
        with contextlib.suppress(OSError):
            os.makedirs(os.path.dirname(dst))
        os.rename(target, dst)
        logger.debug('Moved package to: %s', dst)

    # Add package to set
    package_set.packages.add(package.id)

    return return_message(cmd, errmfs.ok())
