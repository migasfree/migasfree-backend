# -*- coding: utf-8 -*-

# Copyright (c) 2016-2022 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2016-2022 Alberto Gacías <alberto@migasfree.org>
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

from django_filters import rest_framework as filters

from .models import (
    Device, Driver, Manufacturer,
    Capability, Type, Connection,
    Logical, Model,
)


class CapabilityFilter(filters.FilterSet):
    class Meta:
        model = Capability
        fields = {
            'id': ['exact', 'in'],
            'name': ['exact', 'icontains'],
        }


class ConnectionFilter(filters.FilterSet):
    class Meta:
        model = Connection
        fields = {
            'id': ['exact', 'in'],
            'name': ['exact', 'icontains'],
            'device_type__id': ['exact'],
            'device_type__name': ['exact', 'icontains'],
            'model__id': ['exact'],
        }


class DeviceFilter(filters.FilterSet):
    class Meta:
        model = Device
        fields = {
            'id': ['exact', 'in'],
            'model__id': ['exact'],
            'model__name': ['exact', 'icontains'],
            'model__manufacturer__id': ['exact'],
            'model__manufacturer__name': ['exact', 'icontains'],
            'connection__id': ['exact'],
            'connection__name': ['exact', 'icontains'],
        }


class DriverFilter(filters.FilterSet):
    class Meta:
        model = Driver
        fields = {
            'id': ['exact', 'in'],
            'project__id': ['exact'],
            'project__name': ['exact', 'icontains'],
            'model__id': ['exact'],
            'model__name': ['exact', 'icontains'],
            'capability__id': ['exact'],
            'capability__name': ['exact', 'icontains'],
        }


class ManufacturerFilter(filters.FilterSet):
    class Meta:
        model = Manufacturer
        fields = {
            'id': ['exact', 'in'],
            'name': ['exact', 'icontains'],
        }


class TypeFilter(filters.FilterSet):
    class Meta:
        model = Type
        fields = {
            'id': ['exact', 'in'],
            'name': ['exact', 'icontains'],
        }


class LogicalFilter(filters.FilterSet):
    class Meta:
        model = Logical
        fields = {
            'id': ['exact', 'in'],
            'device__id': ['exact'],
            'device__name': ['exact', 'icontains'],
            'device__model__id': ['exact'],
            'capability__id': ['exact'],
            'capability__name': ['exact', 'icontains'],
            'attributes__id': ['exact'],
        }


class ModelFilter(filters.FilterSet):
    class Meta:
        model = Model
        fields = {
            'id': ['exact', 'in'],
            'name': ['exact', 'icontains'],
            'manufacturer__id': ['exact'],
            'manufacturer__name': ['exact', 'icontains'],
            'device_type__id': ['exact'],
            'device_type__name': ['exact', 'icontains'],
            'connections__id': ['exact'],
            'drivers__project__id': ['exact'],
        }
