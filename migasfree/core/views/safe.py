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

import contextlib
import os

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from ...utils import save_tempfile
from ..mixins import SafeConnectionMixin
from ..models import Deployment, Package, PackageSet, Project, Store
from ..pms import tasks


class SafePackagerConnectionMixin(SafeConnectionMixin):
    decrypt_key = settings.MIGASFREE_PRIVATE_KEY
    verify_key = settings.MIGASFREE_PACKAGER_PUB_KEY

    sign_key = settings.MIGASFREE_PRIVATE_KEY
    encrypt_key = settings.MIGASFREE_PACKAGER_PUB_KEY


def check_repository_metadata(package_id):
    for deploy in Deployment.objects.filter(available_packages__id=package_id):
        tasks.create_repository_metadata.apply_async(
            queue=f'pms-{deploy.pms().name}', kwargs={'payload': deploy.get_repository_metadata_payload()}
        )


@extend_schema(tags=['safe'])
@permission_classes((permissions.AllowAny,))
@throttle_classes([UserRateThrottle])
class SafePackageViewSet(SafePackagerConnectionMixin, viewsets.ViewSet):
    def get_package_data(self, _file, project):
        name, version, architecture = Package.normalized_name(_file.name)
        if not name:
            package_path = save_tempfile(_file)
            response = tasks.package_metadata.apply_async(
                kwargs={'pms_name': project.pms, 'package': package_path}, queue=f'pms-{project.pms}'
            ).get()
            os.remove(package_path)
            if response['name']:
                name = response['name']
                version = response['version']
                architecture = response['architecture']

        return name, version, architecture

    @extend_schema(
        description=(
            'Accepts an uploaded file together with claim information (project, store, '
            'and a flag indicating if the file represents a package). The endpoint '
            'stores the file, creates or updates the related ``Package`` record and '
            'updates repository metadata when necessary (requires JWT auth).'
        ),
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {'type': 'string', 'format': 'binary', 'description': 'The package file to upload'},
                    'project': {'type': 'string', 'description': 'Name of the project'},
                    'store': {'type': 'string', 'description': 'Name of the store'},
                    'is_package': {'type': 'boolean', 'description': 'Indicates if file is a package or regular file'},
                },
                'required': ['file', 'project', 'store'],
            }
        },
        responses={
            status.HTTP_200_OK: {'description': gettext('Data received')},
            status.HTTP_404_NOT_FOUND: {'description': 'Project not found'},
        },
    )
    def create(self, request):
        """
        claims = {
            'project': project_name,
            'store': store_name,
            'is_package': true|false
        }
        """

        claims = self.get_claims(request.data)
        project = get_object_or_404(Project, name=claims.get('project'))

        store, _ = Store.objects.get_or_create(name=claims.get('store'), project=project)

        _file = request.FILES.get('file')

        Package.handle_uploaded_file(_file, Package.path(project.slug, store.slug, _file.name))

        if claims.get('is_package'):
            package = Package.objects.filter(fullname=_file.name, project=project).first()
            name, version, architecture = self.get_package_data(_file, project)
            if package:
                package.update_store(store)
                if name and version and architecture:
                    package.update_package_data(name, version, architecture)

                check_repository_metadata(package.id)
            else:
                Package.objects.create(
                    fullname=_file.name,
                    name=name,
                    version=version,
                    architecture=architecture,
                    project=project,
                    store=store,
                    file_=_file,
                )

        return Response(self.create_response(gettext('Data received')), status=status.HTTP_200_OK)

    @extend_schema(
        description='Creates or updates a package set and store an uploaded package file (requires JWT auth).',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {'type': 'string', 'format': 'binary', 'description': 'The package file to upload'},
                    'project': {'type': 'string', 'description': 'Name of the project'},
                    'store': {'type': 'string', 'description': 'Name of the store'},
                    'packageset': {'type': 'string', 'description': 'Name of the package set'},
                    'path': {
                        'type': 'string',
                        'description': 'Optional relative path inside the store where the file should be moved',
                    },
                },
                'required': ['file', 'project', 'store', 'packageset'],
            }
        },
        responses={
            status.HTTP_200_OK: {'description': gettext('Data received')},
        },
    )
    @action(methods=['post'], detail=False, url_path='set')
    def packageset(self, request):
        """
        claims = {
            'project': project_name,
            'store': store_name,
            'packageset': string,
            'path': string
        }
        """

        claims = self.get_claims(request.data)
        project = get_object_or_404(Project, name=claims.get('project'))
        packageset = os.path.basename(claims.get('packageset'))

        store, _ = Store.objects.get_or_create(name=claims.get('store'), project=project)

        _file = request.FILES.get('file')

        package_set = PackageSet.objects.filter(name=packageset, project=project).first()
        if package_set:
            package_set.update_store(store)
        else:
            package_set = PackageSet.objects.create(
                name=packageset,
                project=project,
                store=store,
            )

        target = Package.path(project.slug, store.slug, _file.name)
        Package.handle_uploaded_file(_file, target)

        package = Package.objects.filter(fullname=_file, project=project).first()
        name, version, architecture = self.get_package_data(_file, project)
        if package:
            package.update_store(store)
            if name and version and architecture:
                package.update_package_data(name, version, architecture)

            check_repository_metadata(package.id)
        else:
            package = Package.objects.create(
                fullname=_file.name,
                name=name,
                version=version,
                architecture=architecture,
                project=project,
                store=store,
                file_=_file,
            )

        # if exists path move it
        if claims.get('path'):
            dst = os.path.join(Store.path(project.slug, store.slug), claims.get('path'), _file.name)
            with contextlib.suppress(OSError):
                os.makedirs(os.path.dirname(dst))
            os.rename(target, dst)

        package_set.packages.add(package.id)

        return Response(self.create_response(gettext('Data received')), status=status.HTTP_200_OK)

    @extend_schema(
        description='Creates a repository entry for an existing package set (requires JWT auth).',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'project': {'type': 'string', 'description': 'Name of the project'},
                    'packageset': {'type': 'string', 'description': 'Fullname of the package set'},
                },
                'required': ['project', 'packageset'],
            }
        },
        responses={
            status.HTTP_200_OK: {'description': gettext('Data received')},
            status.HTTP_400_BAD_REQUEST: {'description': gettext('Malformed claims')},
            status.HTTP_404_NOT_FOUND: {'description': 'Project or PackageSet not found'},
        },
    )
    @action(methods=['post'], detail=False, url_path='repos')
    def create_repository(self, request):
        """
        claims = {
            'project': project_name,
            'packageset': name,
        }
        """

        claims = self.get_claims(request.data)
        if not claims or 'project' not in claims or 'packageset' not in claims:
            return Response(self.create_response(gettext('Malformed claims')), status=status.HTTP_400_BAD_REQUEST)

        project = get_object_or_404(Project, name=claims.get('project'))
        package = get_object_or_404(Package, fullname=os.path.basename(claims.get('packageset')), project=project)

        check_repository_metadata(package.id)

        return Response(self.create_response(gettext('Data received')), status=status.HTTP_200_OK)
