# -*- coding: utf-8 -*-

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

from django_filters import rest_framework as filters

from .models import Device, Driver, Manufacturer, Capability, Type


class CapabilityFilter(filters.FilterSet):
    class Meta:
        model = Capability
        fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains'],
        }


class DeviceFilter(filters.FilterSet):
    class Meta:
        model = Device
        fields = ['model__id', 'model__name']


class DriverFilter(filters.FilterSet):
    class Meta:
        model = Driver
        fields = [
            'project__id', 'project__name',
            'model__id', 'model__name',
            'capability__id', 'capability__name'
        ]


class ManufacturerFilter(filters.FilterSet):
    class Meta:
        model = Manufacturer
        fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains'],
        }


class TypeFilter(filters.FilterSet):
    class Meta:
        model = Type
        fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains'],
        }
