# Copyright (c) 2017-2025 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2017-2025 Alberto Gacías <alberto@migasfree.org>
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

from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import parsers, permissions, status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ..client.models import Computer
from ..core.permissions import PublicPermission
from ..core.views import ExportViewSet, MigasViewSet
from ..mixins import DatabaseCheckMixin
from . import models, serializers
from .filters import (
    ApplicationFilter,
    CategoryFilter,
    PackagesByProjectFilter,
    PolicyFilter,
    PolicyGroupFilter,
)


@extend_schema(tags=['catalog'])
@extend_schema(
    parameters=[OpenApiParameter(name='search', location=OpenApiParameter.QUERY, description='Fields: name', type=str)],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class CategoryViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = models.Category.objects.prefetch_related(
        'application_set',
    )
    serializer_class = serializers.CategorySerializer
    filterset_class = CategoryFilter
    permission_classes = (PublicPermission,)
    search_fields = ('name',)
    ordering_fields = '__all__'
    ordering = ('name',)


@extend_schema(tags=['catalog'])
@extend_schema(
    parameters=[OpenApiParameter(name='search', location=OpenApiParameter.QUERY, description='Fields: name', type=str)],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class ApplicationViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = models.Application.objects.select_related(
        'category',
    ).prefetch_related(
        'available_for_attributes',
        'available_for_attributes__property_att',
        'packages_by_project',
        'packages_by_project__project',
    )
    serializer_class = serializers.ApplicationSerializer
    filterset_class = ApplicationFilter
    parser_classes = (parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser)
    permission_classes = (PublicPermission,)
    search_fields = ('name',)
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return serializers.ApplicationWriteSerializer

        return serializers.ApplicationSerializer

    @action(methods=['get'], detail=False)
    def levels(self, request):
        return Response(dict(models.Application.LEVELS), status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def available(self, request):
        """
        :param request:
            cid (computer Id) int,
            category int,
            level int,
            q string (name or description contains...),
            page int
        :return: ApplicationSerializer set
        """
        computer = get_object_or_404(Computer, pk=request.GET.get('cid', 0))
        category = request.GET.get('category', 0)
        level = request.GET.get('level', '')
        query = request.GET.get('q', '')

        results = (
            models.Application.objects
            .select_related('category')
            .prefetch_related(
                'available_for_attributes',
                'packages_by_project__project',
            )
            .filter(
                available_for_attributes__in=computer.sync_attributes.values_list('id', flat=True),
                packages_by_project__project=computer.project,
            )
            .order_by('-score', 'name')
            .distinct()
        )
        if category:
            results = results.filter(category=category)
        if level:
            results = results.filter(level=level)
        if query:
            results = results.filter(Q(name__icontains=query) | Q(description__icontains=query))

        page = self.paginate_queryset(results)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=['catalog'])
@permission_classes((permissions.DjangoModelPermissions,))
class PackagesByProjectViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet):
    queryset = models.PackagesByProject.objects.select_related(
        'application',
        'application__category',
        'project',
        'project__platform',
    )
    serializer_class = serializers.PackagesByProjectSerializer
    filterset_class = PackagesByProjectFilter
    permission_classes = (PublicPermission,)
    ordering = ('application__id', 'project__name')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return serializers.PackagesByProjectWriteSerializer

        return serializers.PackagesByProjectSerializer


@extend_schema(tags=['catalog'])
@extend_schema(
    parameters=[OpenApiParameter(name='search', location=OpenApiParameter.QUERY, description='Fields: name', type=str)],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class PolicyViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = models.Policy.objects.prefetch_related(
        'included_attributes',
        'included_attributes__property_att',
        'excluded_attributes',
        'excluded_attributes__property_att',
        'groups',
        'groups__priority',
    )
    serializer_class = serializers.PolicySerializer
    filterset_class = PolicyFilter
    search_fields = ('name',)
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return serializers.PolicyWriteSerializer

        return serializers.PolicySerializer


@extend_schema(tags=['catalog'])
@permission_classes((permissions.DjangoModelPermissions,))
class PolicyGroupViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet):
    queryset = models.PolicyGroup.objects.select_related(
        'policy',
    ).prefetch_related(
        'included_attributes',
        'excluded_attributes',
        'applications',
    )
    serializer_class = serializers.PolicyGroupSerializer
    filterset_class = PolicyGroupFilter
    ordering = ('policy__id', 'priority')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return serializers.PolicyGroupWriteSerializer

        return serializers.PolicyGroupSerializer
