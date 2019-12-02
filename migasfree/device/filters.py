# -*- coding: utf-8 -*-

# Copyright (c) 2016-2019 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2016-2019 Alberto Gacías <alberto@migasfree.org>
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

from .models import Device, Driver


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
            'feature__id', 'feature__name'
        ]
