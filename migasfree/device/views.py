# -*- coding: utf-8 *-*

# Copyright (c) 2016 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2016 Alberto Gacías <alberto@migasfree.org>
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

from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext
from rest_framework import viewsets, status, filters, mixins
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework_filters import backends

from .models import (
    Connection, Device, Driver,
    Feature, Logical, Manufacturer,
    Model, Type
)
from .filters import DeviceFilter
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
    paginate_by = 100  # FIXME constant


class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = serializers.DriverSerializer
    ordering_fields = '__all__'
    ordering = ('name',)
    paginate_by = 100  # FIXME constant


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
    paginate_by = 100  # FIXME constant


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
    paginate_by = 100  # FIXME constant


class TypeViewSet(viewsets.ModelViewSet):
    queryset = Type.objects.all()
    serializer_class = serializers.TypeSerializer
    ordering_fields = '__all__'
    ordering = ('name',)
