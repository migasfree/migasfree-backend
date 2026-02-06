# Copyright (c) 2016-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2016-2026 Alberto Gacías <alberto@migasfree.org>
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

from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ..client.models import Computer
from ..core.models import Attribute
from ..core.views import ExportViewSet, MigasViewSet
from ..mixins import DatabaseCheckMixin
from . import serializers
from .filters import (
    CapabilityFilter,
    ConnectionFilter,
    DeviceFilter,
    DriverFilter,
    LogicalFilter,
    ManufacturerFilter,
    ModelFilter,
    TypeFilter,
)
from .models import Capability, Connection, Device, Driver, Logical, Manufacturer, Model, Type


@extend_schema(tags=['devices'])
@extend_schema(
    parameters=[OpenApiParameter(name='search', location=OpenApiParameter.QUERY, description='Fields: name', type=str)],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class ConnectionViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Connection.objects.all()
    serializer_class = serializers.ConnectionSerializer
    filterset_class = ConnectionFilter
    search_fields = ['name']
    ordering_fields = '__all__'
    ordering = ('id',)

    def get_queryset(self):
        return self.queryset.select_related('device_type')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return serializers.ConnectionWriteSerializer

        return serializers.ConnectionSerializer


@extend_schema(tags=['devices'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: name, model__name, model__manufacturer__name, data',
            type=str,
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class DeviceViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Device.objects.select_related(
        'model',
        'model__manufacturer',
        'model__device_type',
    ).prefetch_related(
        'available_for_attributes',
        'available_for_attributes__property_att',
        'logical_set',
        'logical_set__capability',
    )
    serializer_class = serializers.DeviceSerializer
    filterset_class = DeviceFilter
    search_fields = ['name', 'model__name', 'model__manufacturer__name', 'data']
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return serializers.DeviceWriteSerializer

        return serializers.DeviceSerializer

    def get_queryset(self):
        if self.request is None:
            return Device.objects.none()

        return Device.objects.scope(self.request.user.userprofile).with_metadata(self.request.user.userprofile)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})

        return context

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

        results = Device.objects.available_for_computer(computer, query, request.user.userprofile)

        page = self.paginate_queryset(results)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True)
    def replacement(self, request, pk=None):
        """
        Input: {
            'target': id
        }
        Exchanges computers from logical devices
        """
        source = self.get_object()
        target = get_object_or_404(Device, id=request.data.get('target'))

        Device.replacement(source, target)

        return Response(status=status.HTTP_200_OK)


@extend_schema(tags=['devices'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search', location=OpenApiParameter.QUERY, description='Fields: name, model__name', type=str
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class DriverViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Driver.objects.select_related(
        'model',
        'model__manufacturer',
        'model__device_type',
        'project',
        'project__platform',
        'capability',
    )
    serializer_class = serializers.DriverSerializer
    filterset_class = DriverFilter
    search_fields = ['name', 'model__name']
    ordering_fields = '__all__'
    ordering = ('model', 'project', 'capability')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return serializers.DriverWriteSerializer

        return serializers.DriverSerializer


@extend_schema(tags=['devices'])
@extend_schema(
    parameters=[OpenApiParameter(name='search', location=OpenApiParameter.QUERY, description='Fields: name', type=str)],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class CapabilityViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Capability.objects.all()
    serializer_class = serializers.CapabilitySerializer
    filterset_class = CapabilityFilter
    search_fields = ['name']
    ordering_fields = '__all__'
    ordering = ('name',)


@extend_schema(tags=['devices'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: device__name, device__model__name, '
            'device__model__manufacturer__name, capability__name',
            type=str,
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class LogicalViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Logical.objects.all()
    serializer_class = serializers.LogicalSerializer
    filterset_class = LogicalFilter
    search_fields = [
        'device__name',
        'device__model__name',
        'device__model__manufacturer__name',
        'capability__name',
    ]
    ordering_fields = '__all__'
    ordering = ('device__name',)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return serializers.LogicalWriteSerializer

        return serializers.LogicalSerializer

    def get_queryset(self):
        if self.request is None:
            return Logical.objects.none()

        qs = Attribute.objects.scope(self.request.user.userprofile)

        return Logical.objects.scope(self.request.user.userprofile).prefetch_related(
            Prefetch('attributes', queryset=qs),
            'attributes__property_att',
        )

    @action(methods=['get'], detail=False)
    def available(self, request):
        """
        :param request:
            cid (computer Id) int,
            q string (name or data contains...),
            did (device Id) int,
            page int
        :return: LogicalSerializer set
        """
        computer = get_object_or_404(Computer, pk=request.GET.get('cid', 0))
        query = request.GET.get('q', '')
        device = request.GET.get('did', 0)

        results = (
            Logical.objects.filter(
                device__available_for_attributes__in=computer.sync_attributes.values_list('id', flat=True)
            )
            .order_by('device__name', 'capability__name')
            .distinct()
        )
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


@extend_schema(tags=['devices'])
@extend_schema(
    parameters=[OpenApiParameter(name='search', location=OpenApiParameter.QUERY, description='Fields: name', type=str)],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class ManufacturerViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Manufacturer.objects.all()
    serializer_class = serializers.ManufacturerSerializer
    filterset_class = ManufacturerFilter
    search_fields = ['name']
    ordering_fields = '__all__'
    ordering = ('name',)


@extend_schema(tags=['devices'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search', location=OpenApiParameter.QUERY, description='Fields: name, manufacturer__name', type=str
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class ModelViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Model.objects.all()
    serializer_class = serializers.ModelSerializer
    filterset_class = ModelFilter
    search_fields = ['name', 'manufacturer__name']
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return serializers.ModelWriteSerializer

        return serializers.ModelSerializer

    def get_queryset(self):
        if self.request is None:
            return Model.objects.none()

        return (
            super()
            .get_queryset()
            .select_related('device_type', 'manufacturer')
            .prefetch_related('connections')
            .distinct()
        )


@extend_schema(tags=['devices'])
@extend_schema(
    parameters=[OpenApiParameter(name='search', location=OpenApiParameter.QUERY, description='Fields: name', type=str)],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class TypeViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Type.objects.all()
    serializer_class = serializers.TypeSerializer
    filterset_class = TypeFilter
    search_fields = ['name']
    ordering_fields = '__all__'
    ordering = ('name',)
