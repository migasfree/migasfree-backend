# -*- coding: utf-8 *-*

# Copyright (c) 2016-2020 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2016-2020 Alberto Gacías <alberto@migasfree.org>
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
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ..client.models import Computer
from ..core.views import MigasViewSet

from .models import (
    Connection, Device, Driver,
    Capability, Logical, Manufacturer,
    Model, Type
)
from .filters import DeviceFilter, DriverFilter, ManufacturerFilter
from . import serializers


@permission_classes((permissions.DjangoModelPermissions,))
class ConnectionViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = Connection.objects.all()
    serializer_class = serializers.ConnectionSerializer
    ordering_fields = '__all__'
    ordering = ('id',)

    def get_queryset(self):
        return self.queryset.select_related('type')


@permission_classes((permissions.DjangoModelPermissions,))
class DeviceViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = Device.objects.all()
    serializer_class = serializers.DeviceSerializer
    filterset_class = DeviceFilter
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return serializers.DeviceWriteSerializer

        return serializers.DeviceSerializer

    def get_queryset(self):
        return self.queryset.select_related(
            'connection', 'connection__type',
            'model', 'model__manufacturer', 'model__type',
        )

    @action(methods=['get'], detail=False)
    def available(self, request):
        """
        :param request:
            cid (computer Id) int,
            q string (name or data contains...),
            page int
        :return: DeviceSerializer set
        """
        computer = get_object_or_404(Computer, pk=request.GET.get('cid', 0))
        query = request.GET.get('q', '')

        results = Device.objects.filter(
            available_for_attributes__in=computer.sync_attributes.values_list('id', flat=True)
        ).order_by('name', 'model__name').distinct()
        if query:
            results = results.filter(Q(name__icontains=query) | Q(data__icontains=query))

        page = self.paginate_queryset(results)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@permission_classes((permissions.DjangoModelPermissions,))
class DriverViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = Driver.objects.all()
    serializer_class = serializers.DriverSerializer
    filterset_class = DriverFilter
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return serializers.DriverWriteSerializer

        return serializers.DriverSerializer


@permission_classes((permissions.DjangoModelPermissions,))
class CapabilityViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = Capability.objects.all()
    serializer_class = serializers.CapabilitySerializer
    ordering_fields = '__all__'
    ordering = ('name',)


@permission_classes((permissions.DjangoModelPermissions,))
class LogicalViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = Logical.objects.all()
    serializer_class = serializers.LogicalSerializer
    ordering_fields = '__all__'
    ordering = ('device__name',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return serializers.LogicalWriteSerializer

        return serializers.LogicalSerializer

    def get_queryset(self):
        return self.queryset.select_related('device', 'capability')

    @action(methods=['get'], detail=False)
    def available(self, request):
        """
        :param request:
            cid (computer Id) int,
            q string (name or data contains...),
            did (device Id) int,
            page int
        :return: DeviceLogicalSerializer set
        """
        computer = get_object_or_404(Computer, pk=request.GET.get('cid', 0))
        query = request.GET.get('q', '')
        device = request.GET.get('did', 0)

        results = Logical.objects.filter(
            device__available_for_attributes__in=computer.sync_attributes.values_list('id', flat=True)
        ).order_by('device__name', 'capability__name').distinct()
        if query:
            results = results.filter(Q(device__name__icontains=query) | Q(device__data__icontains=query))
        if device:
            results = results.filter(device__id=device)

        page = self.paginate_queryset(results)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@permission_classes((permissions.DjangoModelPermissions,))
class ManufacturerViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = Manufacturer.objects.all()
    serializer_class = serializers.ManufacturerSerializer
    filterset_class = ManufacturerFilter
    search_fields = ['name']
    ordering_fields = '__all__'
    ordering = ('name',)


@permission_classes((permissions.DjangoModelPermissions,))
class ModelViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = Model.objects.all()
    serializer_class = serializers.ModelSerializer
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return serializers.ModelWriteSerializer

        return serializers.ModelSerializer


@permission_classes((permissions.DjangoModelPermissions,))
class TypeViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = Type.objects.all()
    serializer_class = serializers.TypeSerializer
    ordering_fields = '__all__'
    ordering = ('name',)
