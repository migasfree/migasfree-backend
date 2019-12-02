# -*- coding: utf-8 -*-

# Copyright (c) 2015-2019 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2019 Alberto Gacías <alberto@migasfree.org>
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
    Deployment, Package, ClientAttribute, ServerAttribute,
    Project, ScheduleDelay, Store, AttributeSet, Property,
)


class AttributeSetFilter(filters.FilterSet):
    class Meta:
        model = AttributeSet
        fields = ['id', 'name', 'enabled']


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
        fields = ['id', 'name', 'deployment__id', 'store__id']


class ProjectFilter(filters.FilterSet):
    class Meta:
        model = Project
        fields = ['id', 'platform__id', 'name']


class PropertyFilter(filters.FilterSet):
    class Meta:
        model = Property
        fields = ['id', 'name', 'enabled', 'sort']


class ClientAttributeFilter(filters.FilterSet):
    class Meta:
        model = ClientAttribute
        fields = ['id', 'property_att__id', 'property_att__prefix', 'value', 'property_att__sort']


class ServerAttributeFilter(filters.FilterSet):
    class Meta:
        model = ServerAttribute
        fields = ['id', 'property_att__id', 'property_att__prefix', 'value', 'property_att__sort']


class ScheduleDelayFilter(filters.FilterSet):
    class Meta:
        model = ScheduleDelay
        fields = ['schedule__id', 'schedule__name']


class StoreFilter(filters.FilterSet):
    class Meta:
        model = Store
        fields = ['id', 'name', 'project__id']
