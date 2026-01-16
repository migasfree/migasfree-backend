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

from django.utils.text import slugify
from django.utils.translation import gettext
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import permission_classes
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
    queryset = Platform.objects.all()
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
    queryset = Project.objects.all()
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
    queryset = Store.objects.all()
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
