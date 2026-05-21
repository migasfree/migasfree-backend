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

import requests
from django.http import HttpResponse
from django.utils.text import slugify
from django.utils.translation import gettext
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from ....mixins import DatabaseCheckMixin
from ...filters import PlatformFilter, ProjectFilter, StoreFilter
from ...models import Platform, Project, Store
from ...serializers import (
    PlatformSerializer,
    ProjectSerializer,
    ProjectWriteSerializer,
    StoreSerializer,
    StoreWriteSerializer,
)
from .base import ExportViewSet, MigasViewSet


@extend_schema(tags=['platforms'])
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
class PlatformViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Platform.objects.prefetch_related('project_set')
    serializer_class = PlatformSerializer
    filterset_class = PlatformFilter
    ordering_fields = '__all__'
    ordering = ('name',)
    search_fields = ('name',)

    def get_queryset(self):
        if self.request is None:
            return Platform.objects.none()

        return Platform.objects.scope(self.request.user.userprofile)


@extend_schema(tags=['projects'])
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
class ProjectViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Project.objects.select_related(
        'platform',
    ).prefetch_related(
        'deployment_set',
        'package_set',
        'store_set',
    )
    serializer_class = ProjectSerializer
    filterset_class = ProjectFilter
    ordering_fields = '__all__'
    ordering = ('name',)
    search_fields = ('name',)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return ProjectWriteSerializer

        return ProjectSerializer

    def get_queryset(self):
        if self.request is None:
            return Project.objects.none()

        return Project.objects.scope(self.request.user.userprofile)

    def create(self, request, *args, **kwargs):
        data = dict(request.data)

        slug = slugify(data['name'])
        if Project.objects.filter(slug=slug).exists():
            return Response(
                {'detail': gettext('Project slug already exists')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().create(request, *args, **kwargs)

    @extend_schema(
        request=inline_serializer(
            name='MciImportRequest',
            fields={
                'template_id': serializers.CharField(help_text='The MCI template ID to import (e.g. debian-13)'),
            },
        )
    )
    @action(detail=True, methods=['post'], url_path='template-import')
    def template_import(self, request, pk=None):
        project_id = pk
        template_id = request.data.get('template_id')

        if not template_id:
            return Response({'error': 'template_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Fetch template data from manager
        headers = {}
        if request.auth:
            headers['Authorization'] = f'Bearer {request.auth}'

        try:
            manager_url = f'http://manager:8080/manager/v1/internal/mci/templates/{template_id}'
            response = requests.get(manager_url, headers=headers, timeout=10.0)
            response.raise_for_status()
            template_data = response.json()
        except Exception as e:
            raise ValidationError(f'Failed to fetch template {template_id} from manager: {e!s}')

        # 2. Create or update Config
        from migasfree.mci.models import Config, Flavour  # noqa: avoid circular import
        from migasfree.mci.serializers import ConfigSerializer  # noqa: avoid circular import

        config, created = Config.objects.update_or_create(
            project_id=project_id,
            defaults={
                'template_id': template_id,
                'base_os': template_data.get('base_os', ''),
                'dockerfile': template_data.get('dockerfile', ''),
                'partition': template_data.get('partition', ''),
            },
        )

        # 3. Create default Flavour
        _, f_created = Flavour.objects.get_or_create(
            config=config,
            name='Default',
            defaults={
                'user': 'migasfree',
                'password': 'migasfree-password',
                'hostname': config.project.name.lower().replace(' ', '-'),
            },
        )

        # 4. Automatically trigger the Manager to import deployments, applications, stores and packages
        manager_import_result = None
        try:
            manager_url = (
                f'http://manager:8080/manager/v1/internal/mci/projects/{project_id}/import?template_id={template_id}'
            )
            response = requests.post(manager_url, headers=headers, timeout=120.0)
            if response.ok:
                manager_import_result = response.json()
            else:
                manager_import_result = {
                    'error': f'Manager responded with HTTP {response.status_code}',
                    'details': response.text,
                }
        except Exception as e:
            manager_import_result = {'error': f'Could not connect to manager: {e!s}'}

        return Response(
            {
                'config': ConfigSerializer(config, context={'request': request}).data,
                'config_created': created,
                'flavour_created': f_created,
                'manager_import': manager_import_result,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=['get'], url_path='template-export')
    def template_export(self, request, pk=None):
        project_id = pk

        try:
            headers = {}
            if request.auth:
                headers['Authorization'] = f'Bearer {request.auth}'

            manager_url = f'http://manager:8080/manager/v1/internal/mci/projects/{project_id}/export'
            headers['Accept'] = 'application/json'
            response = requests.get(manager_url, headers=headers, timeout=60.0)
            if response.ok:
                return HttpResponse(response.content, content_type='application/json')
            else:
                return Response(
                    {'error': f'Manager responded with HTTP {response.status_code}', 'details': response.text},
                    status=response.status_code,
                )
        except Exception as e:
            return Response(
                {'error': f'Could not connect to manager: {e!s}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(tags=['stores'])
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
class StoreViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Store.objects.select_related(
        'project',
        'project__platform',
    ).prefetch_related(
        'package_set',
        'packageset_set',
    )
    serializer_class = StoreSerializer
    filterset_class = StoreFilter
    ordering_fields = '__all__'
    ordering = ('name', 'project__name')
    search_fields = ('name',)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return StoreWriteSerializer

        return StoreSerializer

    def get_queryset(self):
        if self.request is None:
            return Store.objects.none()

        return Store.objects.scope(self.request.user.userprofile)
