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
        summary="Fetch the MGI templates catalog from the manager service",
        description="Retrieve a list of all MGI templates available in the catalog.",
    )
    @action(detail=False, methods=['get'], url_path='templates')
    def templates(self, request):
        """Fetch the MGI templates catalog from the manager service."""
        headers = {}
        if request.auth:
            headers['Authorization'] = f'Bearer {request.auth}'

        try:
            manager_url = 'http://manager:8080/manager/v1/internal/mgi/projects/templates'
            response = requests.get(manager_url, headers=headers, timeout=15.0)

            if response.ok:
                return Response(response.json(), status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': f'Manager responded with HTTP {response.status_code}', 'details': response.text},
                    status=response.status_code,
                )
        except Exception as e:
            return Response(
                {'error': f'Could not connect to manager: {e!s}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    def _perform_template_import(self, request, project, template_id, origin=None):
        # 1. Fetch template data from manager
        headers = {}
        if request.auth:
            headers['Authorization'] = f'Bearer {request.auth}'

        try:
            manager_url = f'http://manager:8080/manager/v1/internal/mgi/projects/templates/{template_id}'
            params = {}
            if origin:
                params['origin'] = origin
            response = requests.get(manager_url, headers=headers, params=params, timeout=10.0)
            response.raise_for_status()
            template_data = response.json()
        except Exception as e:
            raise ValidationError(f'Failed to fetch template {template_id} from manager: {e!s}') from e

        # Check if the template was not found in the manager catalog
        if not template_data or template_data.get('base_os') is None:
            origin_str = f" in origin '{origin}'" if origin else ''
            raise ValidationError(
                f"Template '{template_id}' was not found{origin_str}. Please verify that the template exists and is published."
            )

        # Update Project fields from template metadata (platform, pms, architecture)
        modified_fields = []
        platform_name = template_data.get('platform')
        if platform_name:
            platform_obj, _ = Platform.objects.get_or_create(name=platform_name)
            if project.platform != platform_obj:
                project.platform = platform_obj
                modified_fields.append('platform')

        pms_val = template_data.get('pms')
        if pms_val and project.pms != pms_val:
            project.pms = pms_val
            modified_fields.append('pms')

        arch_val = template_data.get('architecture')
        if arch_val and project.architecture != arch_val:
            project.architecture = arch_val
            modified_fields.append('architecture')

        if modified_fields:
            project.save(update_fields=modified_fields)

        # 2. Create or update Config
        from migasfree.mgi.models import Config, Flavour  # avoid circular import
        from migasfree.mgi.serializers import ConfigSerializer  # avoid circular import

        config, created = Config.objects.get_or_create(
            project_id=project.id,
            defaults={
                'template_id': template_id,
                'base_os': template_data.get('base_os') or '',
                'partition': template_data.get('partition') or '',
                'config': {'dockerfile': template_data.get('dockerfile') or ''},
            },
        )
        if not created:
            config.template_id = template_id
            config.base_os = template_data.get('base_os') or ''
            config.partition = template_data.get('partition') or ''
            if not isinstance(config.config, dict):
                config.config = {}
            config.config['dockerfile'] = template_data.get('dockerfile') or ''
            config.config = dict(config.config)
            config.save()

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
                f'http://manager:8080/manager/v1/internal/mgi/projects/{project.id}/import?template_id={template_id}'
            )
            if origin:
                manager_url += f'&origin={origin}'
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

    @extend_schema(
        description=(
            "Import an MGI template to either create a new project or update an existing one.\n\n"
            "To create a new project:\n"
            "- Pass `project_name` (string)\n\n"
            "To update an existing project:\n"
            "- Pass `project_id` (integer)\n\n"
            "Optional parameter:\n"
            "- Pass `origin` (string: 'local' or 'remote') to specify the template source catalog."
        ),
        request=inline_serializer(
            name='MgiImportListRequest',
            fields={
                'template_id': serializers.CharField(help_text='The MGI template ID to import (e.g. debian-13)'),
                'project_name': serializers.CharField(
                    required=False,
                    allow_null=True,
                    help_text='The name of the new project to create',
                ),
                'project_id': serializers.IntegerField(
                    required=False,
                    allow_null=True,
                    help_text='The ID of an existing project to import into',
                ),
                'origin': serializers.CharField(
                    required=False,
                    allow_null=True,
                    help_text='The origin of the template (local or remote)',
                ),
            },
        )
    )
    @action(detail=False, methods=['post'], url_path='template-import')
    def template_import(self, request):
        template_id = request.data.get('template_id')
        project_name = request.data.get('project_name')
        project_id = request.data.get('project_id')
        origin = request.data.get('origin')

        if not template_id:
            return Response({'error': 'template_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not project_name and not project_id:
            return Response(
                {'error': 'Either project_name (to create a new project) or project_id is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if project_id:
            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                return Response({'error': f'Project with ID {project_id} does not exist'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Check if project name already exists
            if Project.objects.filter(name=project_name).exists():
                return Response(
                    {'error': f"A project with name '{project_name}' already exists"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create new project with temporary default values (they will be updated from template)
            try:
                headers = {}
                if request.auth:
                    headers['Authorization'] = f'Bearer {request.auth}'

                manager_url = f'http://manager:8080/manager/v1/internal/mgi/projects/templates/{template_id}'
                params = {}
                if origin:
                    params['origin'] = origin
                response = requests.get(manager_url, headers=headers, params=params, timeout=10.0)
                response.raise_for_status()
                template_data = response.json()
            except Exception as e:
                raise ValidationError(f'Failed to fetch template {template_id} from manager: {e!s}') from e

            if not template_data or template_data.get('base_os') is None:
                origin_str = f" in origin '{origin}'" if origin else ''
                raise ValidationError(
                    f"Template '{template_id}' was not found{origin_str}. Please verify that the template exists and is published."
                )

            # Get or create platform
            platform_name = template_data.get('platform') or 'debian'  # default fallback
            platform_obj, _ = Platform.objects.get_or_create(name=platform_name)

            pms_val = template_data.get('pms') or 'apt'  # default fallback
            arch_val = template_data.get('architecture') or 'amd64'  # default fallback

            project = Project.objects.create(
                name=project_name,
                pms=pms_val,
                architecture=arch_val,
                platform=platform_obj,
                auto_register_computers=False,
            )

        # Now perform the rest of the template import!
        return self._perform_template_import(request, project, template_id, origin)

    @extend_schema(
        description="Export a project's deployments, stores, and packages to the template catalog.",
        request=inline_serializer(
            name='MgiExportListRequest',
            fields={
                'project_id': serializers.IntegerField(
                    help_text='The ID of the project to export'
                )
            },
        ),
    )
    @action(detail=False, methods=['post'], url_path='template-export')
    def template_export(self, request):
        project_id = request.data.get('project_id')

        if not project_id:
            return Response(
                {'error': 'project_id is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Check if project exists
            Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {'error': f'Project with ID {project_id} does not exist'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            headers = {}
            if request.auth:
                headers['Authorization'] = f'Bearer {request.auth}'

            manager_url = f'http://manager:8080/manager/v1/internal/mgi/projects/{project_id}/export'
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
