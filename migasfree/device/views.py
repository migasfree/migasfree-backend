# -*- coding: utf-8 *-*

# Copyright (c) 2016-2018 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2016-2018 Alberto Gacías <alberto@migasfree.org>
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
from rest_framework import viewsets, filters, status
from rest_framework_filters import backends
from rest_framework.decorators import action
from rest_framework.response import Response

from migasfree.client.models import Computer

from .models import (
    Connection, Device, Driver,
    Feature, Logical, Manufacturer,
    Model, Type
)
from .filters import DeviceFilter, DriverFilter
from . import serializers


class ConnectionViewSet(viewsets.ModelViewSet):
    queryset = Connection.objects.all()
    serializer_class = serializers.ConnectionSerializer
    ordering_fields = '__all__'
    ordering = ('id',)


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = serializers.DeviceSerializer
    filter_class = DeviceFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return serializers.DeviceWriteSerializer

        return serializers.DeviceSerializer

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


class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = serializers.DriverSerializer
    filter_class = DriverFilter
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return serializers.DriverWriteSerializer

        return serializers.DriverSerializer


class FeatureViewSet(viewsets.ModelViewSet):
    queryset = Feature.objects.all()
    serializer_class = serializers.FeatureSerializer
    ordering_fields = '__all__'
    ordering = ('name',)


class LogicalViewSet(viewsets.ModelViewSet):
    queryset = Logical.objects.all()
    serializer_class = serializers.LogicalSerializer
    ordering_fields = '__all__'
    ordering = ('device__name',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return serializers.LogicalWriteSerializer

        return serializers.LogicalSerializer

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
        ).order_by('device__name', 'feature__name').distinct()
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


class ManufacturerViewSet(viewsets.ModelViewSet):
    queryset = Manufacturer.objects.all()
    serializer_class = serializers.ManufacturerSerializer
    ordering_fields = '__all__'
    ordering = ('name',)


class ModelViewSet(viewsets.ModelViewSet):
    queryset = Model.objects.all()
    serializer_class = serializers.ModelSerializer
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return serializers.ModelWriteSerializer

        return serializers.ModelSerializer


class TypeViewSet(viewsets.ModelViewSet):
    queryset = Type.objects.all()
    serializer_class = serializers.TypeSerializer
    ordering_fields = '__all__'
    ordering = ('name',)
