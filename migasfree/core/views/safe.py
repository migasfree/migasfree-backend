# -*- coding: utf-8 *-*

# Copyright (c) 2015-2022 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2022 Alberto Gacías <alberto@migasfree.org>
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

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...utils import save_tempfile

from .. import tasks
from ..mixins import SafeConnectionMixin
from ..models import Project, Store, Package, PackageSet, Deployment


class SafePackagerConnectionMixin(SafeConnectionMixin):
    decrypt_key = settings.MIGASFREE_PRIVATE_KEY
    verify_key = settings.MIGASFREE_PACKAGER_PUB_KEY

    sign_key = settings.MIGASFREE_PRIVATE_KEY
    encrypt_key = settings.MIGASFREE_PACKAGER_PUB_KEY


@permission_classes((permissions.AllowAny,))
class SafePackageViewSet(SafePackagerConnectionMixin, viewsets.ViewSet):
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

        store, _ = Store.objects.get_or_create(
            name=claims.get('store'),
            project=project
        )

        _file = request.FILES.get('file')

        if claims.get('is_package'):
            package = Package.objects.filter(
                fullname=_file.name,
                project=project
            )
            if package.exists():
                package[0].update_store(store)
            else:
                name, version, architecture = Package.normalized_name(_file.name)
                if not name:
                    package_path = save_tempfile(_file)
                    response = tasks.package_metadata.apply_async(
                        kwargs={
                            'pms_name': project.pms,
                            'package': package_path
                        },
                        queue='pms-{}'.format(project.pms)
                    ).get()
                    os.remove(package_path)
                    if response['name']:
                        name = response['name']
                        version = response['version']
                        architecture = response['architecture']

                Package.objects.create(
                    fullname=_file.name,
                    name=name,
                    version=version,
                    architecture=architecture,
                    project=project,
                    store=store,
                    file_=_file
                )

        Package.handle_uploaded_file(
            _file,
            Package.path(project.slug, store.slug, _file.name)
        )

        return Response(
            self.create_response(gettext('Data received')),
            status=status.HTTP_200_OK
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

        store, _ = Store.objects.get_or_create(
            name=claims.get('store'),
            project=project
        )

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

        package = Package.objects.filter(fullname=_file, project=project).first()
        if package:
            package.update_store(store)
        else:
            name, version, architecture = Package.normalized_name(_file.name)
            if not name:
                package_path = save_tempfile(_file)
                response = tasks.package_metadata.apply_async(
                    kwargs={
                        'pms_name': project.pms,
                        'package': package_path
                    },
                    queue='pms-{}'.format(project.pms)
                ).get()
                os.remove(package_path)
                if response['name']:
                    name = response['name']
                    version = response['version']
                    architecture = response['architecture']

            package = Package.objects.create(
                fullname=_file.name,
                name=name,
                version=version,
                architecture=architecture,
                project=project,
                store=store,
                file_=_file
            )

        target = Package.path(project.slug, store.slug, _file.name)
        Package.handle_uploaded_file(_file, target)

        # if exists path move it
        if claims.get('path'):
            dst = os.path.join(
                Store.path(project.slug, store.slug),
                claims.get('path'),
                _file.name
            )
            try:
                os.makedirs(os.path.dirname(dst))
            except OSError:
                pass
            os.rename(target, dst)

        package_set.packages.add(package.id)

        return Response(
            self.create_response(gettext('Data received')),
            status=status.HTTP_200_OK
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
            return Response(
                self.create_response(gettext('Malformed claims')),
                status=status.HTTP_400_BAD_REQUEST
            )

        project = get_object_or_404(Project, name=claims.get('project'))
        package = get_object_or_404(
            Package,
            fullname=os.path.basename(claims.get('packageset')),
            project=project
        )

        deployments = Deployment.objects.filter(
            available_packages__id=package.id
        )
        for deploy in deployments:
            tasks.create_repository_metadata.apply_async(
                queue='pms-{}'.format(deploy.pms().name),
                kwargs={'deployment_id': deploy.id}
            )

        return Response(
            self.create_response(gettext('Data received')),
            status=status.HTTP_200_OK
        )
