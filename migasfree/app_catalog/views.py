# -*- coding: utf-8 -*-

# Copyright (c) 2017-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2017-2021 Alberto Gacías <alberto@migasfree.org>
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
from rest_framework import viewsets, status, permissions, parsers
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ..core.permissions import PublicPermission
from ..core.views import MigasViewSet
from ..client.models import Computer

from . import models, serializers
from .filters import ApplicationFilter, PackagesByProjectFilter, PolicyFilter


@permission_classes((permissions.DjangoModelPermissions,))
class ApplicationViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = models.Application.objects.all()
    serializer_class = serializers.ApplicationSerializer
    filterset_class = ApplicationFilter
    parser_classes = (parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser)
    permission_classes = (PublicPermission,)
    search_fields = ['name']
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return serializers.ApplicationWriteSerializer

        return serializers.ApplicationSerializer

    @action(methods=['get'], detail=False)
    def levels(self, request):
        return Response(
            dict(models.Application.LEVELS),
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False)
    def categories(self, request):
        return Response(
            dict(models.Application.CATEGORIES),
            status=status.HTTP_200_OK
        )

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

        results = models.Application.objects.filter(
            available_for_attributes__in=computer.sync_attributes.values_list('id', flat=True),
            packages_by_project__project=computer.project
        ).order_by('-score', 'name').distinct()
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


@permission_classes((permissions.DjangoModelPermissions,))
class PackagesByProjectViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = models.PackagesByProject.objects.all()
    serializer_class = serializers.PackagesByProjectSerializer
    filterset_class = PackagesByProjectFilter
    permission_classes = (PublicPermission,)
    ordering = ['application__id', 'project__name']

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return serializers.PackagesByProjectWriteSerializer

        return serializers.PackagesByProjectSerializer


@permission_classes((permissions.DjangoModelPermissions,))
class PolicyViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = models.Policy.objects.all()
    serializer_class = serializers.PolicySerializer
    filterset_class = PolicyFilter

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return serializers.PolicyWriteSerializer

        return serializers.PolicySerializer


@permission_classes((permissions.DjangoModelPermissions,))
class PolicyGroupViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = models.PolicyGroup.objects.all()
    serializer_class = serializers.PolicyGroupSerializer

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return serializers.PolicyGroupWriteSerializer

        return serializers.PolicyGroupSerializer
