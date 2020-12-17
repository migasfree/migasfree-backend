# -*- coding: utf-8 -*-

# Copyright (c) 2015-2020 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2020 Alberto Gacías <alberto@migasfree.org>
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
    Deployment, Package, ClientAttribute, ServerAttribute, Attribute,
    Project, ScheduleDelay, Store, AttributeSet, Property, Platform,
)


class AttributeSetFilter(filters.FilterSet):
    class Meta:
        model = AttributeSet
        fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains'],
            'enabled': ['exact'],
        }


class DeploymentFilter(filters.FilterSet):
    included_attributes = filters.CharFilter(
        field_name='included_attributes__value', lookup_expr='contains'
    )
    excluded_attributes = filters.CharFilter(
        field_name='excluded_attributes__value', lookup_expr='contains'
    )
    available_packages = filters.CharFilter(
        field_name='available_packages__name', lookup_expr='contains'
    )

    class Meta:
        model = Deployment
        fields = ['id', 'name', 'project__id', 'enabled', 'schedule__id']


class PackageFilter(filters.FilterSet):
    class Meta:
        model = Package
        fields = {
            'id': ['exact'],
            'fullname': ['icontains'],
            'name': ['exact', 'icontains'],
            'version': ['exact', 'icontains'],
            'architecture': ['exact', 'icontains'],
            'project__id': ['exact'],
            'deployment__id': ['exact'],
            'store__id': ['exact']
        }


class PlatformFilter(filters.FilterSet):
    class Meta:
        model = Platform
        fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains']
        }


class ProjectFilter(filters.FilterSet):
    class Meta:
        model = Project
        fields = {
            'id': ['exact'],
            'platform__id': ['exact'],
            'name': ['exact', 'icontains'],
            'pms': ['exact', 'icontains'],
            'auto_register_computers': ['exact'],
        }


class PropertyFilter(filters.FilterSet):
    class Meta:
        model = Property
        fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains'],
            'enabled': ['exact'],
            'sort': ['exact'],
            'kind': ['exact'],
        }


class AttributeFilter(filters.FilterSet):
    class Meta:
        model = Attribute
        fields = {
            'id': ['exact'],
            'property_att__id': ['exact'],
            'property_att__prefix': ['exact'],
            'value': ['exact', 'icontains'],
            'description': ['icontains'],
            'property_att__sort': ['exact']
        }


class ClientAttributeFilter(filters.FilterSet):
    class Meta:
        model = ClientAttribute
        fields = {
            'id': ['exact'],
            'property_att__id': ['exact'],
            'property_att__prefix': ['exact'],
            'value': ['exact', 'icontains'],
            'description': ['icontains'],
            'property_att__sort': ['exact'],
        }


class ServerAttributeFilter(filters.FilterSet):
    class Meta:
        model = ServerAttribute
        fields = {
            'id': ['exact'],
            'property_att__id': ['exact'],
            'property_att__prefix': ['exact'],
            'value': ['exact', 'icontains'],
            'description': ['icontains'],
            'property_att__sort': ['exact'],
        }


class ScheduleDelayFilter(filters.FilterSet):
    class Meta:
        model = ScheduleDelay
        fields = ['schedule__id', 'schedule__name']


class StoreFilter(filters.FilterSet):
    class Meta:
        model = Store
        fields = {
            'id': ['exact'],
            'name': ['icontains'],
            'project__id': ['exact']
        }
