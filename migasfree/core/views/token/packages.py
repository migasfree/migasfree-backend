# Copyright (c) 2015-2025 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2025 Alberto Gacías <alberto@migasfree.org>
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

from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, parsers, permissions, status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ....mixins import DatabaseCheckMixin
from ....utils import save_tempfile
from ...filters import PackageFilter, PackageSetFilter
from ...models import Package, PackageSet, Project, Store
from ...pms import tasks
from ...serializers import (
    PackageSerializer,
    PackageSetSerializer,
    PackageSetWriteSerializer,
)
from .base import ExportViewSet, MigasViewSet


@extend_schema(tags=['packages'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: fullname',
            type=str,
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class PackageViewSet(
    DatabaseCheckMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
    MigasViewSet,
    ExportViewSet,
):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    filterset_class = PackageFilter
    parser_classes = (parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser)
    ordering_fields = '__all__'
    ordering = ('fullname', 'version', 'project__name')
    search_fields = ('fullname',)

    def get_queryset(self):
        if self.request is None:
            return Package.objects.none()

        return Package.objects.scope(self.request.user.userprofile)

    def create(self, request, *args, **kwargs):
        data = dict(request.data)

        if 'fullname' not in data and 'files' in data and len(data['files']) > 0:
            data['fullname'] = data['files'][0].name

        if 'name' not in data:
            data['name'], data['version'], data['architecture'] = Package.normalized_name(data['fullname'])

        store = get_object_or_404(Store, pk=data['store'][0])

        if not data['name']:
            package_path = save_tempfile(data['files'][0])
            response = tasks.package_metadata.apply_async(
                kwargs={'pms_name': store.project.pms, 'package': package_path},
                queue=f'pms-{store.project.pms}',
            ).get()
            os.remove(package_path)
            if response['name']:
                data['name'] = response['name']
                data['version'] = response['version']
                data['architecture'] = response['architecture']

        try:
            package = Package.objects.create(
                fullname=data['fullname'],
                name=data['name'],
                version=data['version'],
                architecture=data['architecture'],
                project=store.project,
                store=store,
                file_=data['files'][0],
            )

            serializer = PackageSerializer(package)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response(
                {'detail': gettext('Package already exists')},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def destroy(self, request, pk=None):
        instance = self.get_object()
        self.perform_destroy(instance)

        queryset = self.filter_queryset(self.get_queryset())
        if queryset.filter(pk=instance.pk).exists():
            return Response(
                {'detail': gettext('The element has relations and cannot be removed')},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=False)
    def orphan(self, request):
        """
        Returns packages that are not in any deployment
        """
        serializer = PackageSerializer(Package.objects.filter(deployment__id=None, store__isnull=False), many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def info(self, request, pk=None):
        obj = self.get_object()

        if obj.store is None:
            return Response(
                {'detail': gettext('The package has no store on the server')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response = tasks.package_info.apply_async(
            kwargs={
                'pms_name': obj.project.pms,
                'package': Package.path(obj.project.slug, obj.store.slug, obj.fullname),
            },
            queue=f'pms-{obj.project.pms}',
        ).get()

        return Response({'data': response}, status=status.HTTP_200_OK)


@extend_schema(tags=['package-sets'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: name',
            type=str,
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class PackageSetViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = PackageSet.objects.all()
    serializer_class = PackageSetSerializer
    filterset_class = PackageSetFilter
    parser_classes = (parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser)
    search_fields = ('name',)
    ordering_fields = '__all__'
    ordering = ('project__name', 'name')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return PackageSetWriteSerializer

        return PackageSetSerializer

    def get_queryset(self):
        if self.request is None:
            return PackageSet.objects.none()

        return PackageSet.objects.scope(self.request.user.userprofile).distinct()

    def _upload_packages(self, project, store, files):
        new_pkgs = []
        for file_ in files:
            name, version, architecture = Package.normalized_name(file_.name)
            if not name:
                package_path = save_tempfile(file_)
                response = tasks.package_metadata.apply_async(
                    kwargs={'pms_name': project.pms, 'package': package_path},
                    queue=f'pms-{project.pms}',
                ).get()
                os.remove(package_path)
                if response['name']:
                    name = response['name']
                    version = response['version']
                    architecture = response['architecture']

            if not name or not version or not architecture:
                return {'error': gettext('Package %s has an incorrect name format') % file_.name}

            try:
                pkg = Package.objects.create(
                    fullname=file_.name,
                    name=name,
                    version=version,
                    architecture=architecture,
                    project=project,
                    store=store,
                    file_=file_,
                )
            except IntegrityError:
                return {'error': gettext('Package %s is duplicated in store %s') % (file_.name, store.name)}

            new_pkgs.append(str(pkg.id))

        return new_pkgs

    def create(self, request, *args, **kwargs):
        files = request.data.getlist('files')
        if files:
            project_id = request.data.get('project', 0)
            store_id = request.data.get('store', 0)

            project = Project.objects.get(id=project_id)
            store = Store.objects.get(id=store_id)

            if project and store:
                packages = request.data.getlist('packages', [])
                packages = list(filter(None, packages))
                upload_packages = self._upload_packages(project, store, files)
                if isinstance(upload_packages, dict):
                    return Response(upload_packages, status=status.HTTP_400_BAD_REQUEST)
                packages.extend(upload_packages)
                request.data.setlist('packages', packages)

        return super().create(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        obj = self.get_object()

        files = request.data.getlist('files')
        if files:
            packages = request.data.getlist('packages', [])
            packages = list(filter(None, packages))
            upload_packages = self._upload_packages(obj.project, obj.store, files)
            if isinstance(upload_packages, dict):
                return Response(upload_packages, status=status.HTTP_400_BAD_REQUEST)
            packages.extend(upload_packages)
            request.data.setlist('packages', packages)

        return super().partial_update(request, *args, **kwargs)
