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

from django.utils.translation import gettext
from django_redis import get_redis_connection
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ....mixins import DatabaseCheckMixin
from ...filters import DeploymentFilter
from ...models import Deployment, ExternalSource, InternalSource
from ...pms import tasks
from ...serializers import (
    DeploymentListSerializer,
    DeploymentSerializer,
    DeploymentWriteSerializer,
    ExternalSourceSerializer,
    ExternalSourceWriteSerializer,
    InternalSourceSerializer,
    InternalSourceWriteSerializer,
)
from .base import ExportViewSet, MigasViewSet


@extend_schema(tags=['deployments'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: name, packages_to_install, packages_to_remove,'
            ' default_preincluded_packages, default_included_packages, default_excluded_packages',
            type=str,
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class DeploymentViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Deployment.objects.all()
    serializer_class = DeploymentSerializer
    filterset_class = DeploymentFilter
    search_fields = (
        'name',
        'packages_to_install',
        'packages_to_remove',
        'default_preincluded_packages',
        'default_included_packages',
        'default_excluded_packages',
    )
    ordering_fields = '__all__'
    ordering = ('name', 'project__name')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return DeploymentWriteSerializer

        if self.action == 'list':
            return DeploymentListSerializer

        return DeploymentSerializer

    def get_queryset(self):
        if self.request is None:
            return Deployment.objects.none()

        return Deployment.objects.scope(self.request.user.userprofile)


@extend_schema(tags=['deployments'])
@permission_classes((permissions.DjangoModelPermissions,))
class InternalSourceViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet):
    queryset = InternalSource.objects.all()
    serializer_class = InternalSourceSerializer
    filterset_class = DeploymentFilter
    ordering_fields = '__all__'
    ordering = ('name', 'project__name')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return InternalSourceWriteSerializer

        return InternalSourceSerializer

    def get_queryset(self):
        if self.request is None:
            return InternalSource.objects.none()

        return InternalSource.objects.scope(self.request.user.userprofile)

    @action(methods=['get'], detail=True)
    def metadata(self, request, pk=None):
        deploy = self.get_object()
        tasks.create_repository_metadata.apply_async(
            queue=f'pms-{deploy.pms().name}', kwargs={'deployment_id': deploy.id}
        )

        return Response({'detail': gettext('Operation received')}, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def generating(self, request):
        con = get_redis_connection()
        result = con.smembers('migasfree:watch:repos')

        serializer = DeploymentSerializer(Deployment.objects.filter(pk__in=result), many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=['deployments'])
@permission_classes((permissions.DjangoModelPermissions,))
class ExternalSourceViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet):
    queryset = ExternalSource.objects.all()
    serializer_class = ExternalSourceSerializer
    filterset_class = DeploymentFilter
    ordering_fields = '__all__'
    ordering = ('name', 'project__name')

    def get_queryset(self):
        if self.request is None:
            return ExternalSource.objects.none()

        return ExternalSource.objects.scope(self.request.user.userprofile)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' or self.action == 'partial_update':
            return ExternalSourceWriteSerializer

        return ExternalSourceSerializer
