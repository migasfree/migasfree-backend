# -*- coding: utf-8 -*-

# Copyright (c) 2015-2016 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2016 Alberto Gacías <alberto@migasfree.org>
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

import rest_framework_filters as filters

from .models import (
    Deployment, Package, ClientAttribute, ServerAttribute, Project, Store,
)


class DeploymentFilter(filters.FilterSet):
    included_attributes = filters.CharFilter(
        name='included_attributes__value', lookup_type='contains'
    )
    excluded_attributes = filters.CharFilter(
        name='excluded_attributes__value', lookup_type='contains'
    )
    available_packages = filters.CharFilter(
        name='available_packages__name', lookup_type='contains'
    )

    class Meta:
        model = Deployment
        fields = ['project__id', 'enabled', 'schedule__id']


class PackageFilter(filters.FilterSet):
    class Meta:
        model = Package
        fields = ['deployment__id', 'store__id']


class ProjectFilter(filters.FilterSet):
    class Meta:
        model = Project
        fields = ['platform__id', 'name']


class ClientAttributeFilter(filters.FilterSet):
    class Meta:
        model = ClientAttribute
        fields = ['property_att__id', 'property_att__prefix', 'value']


class ServerAttributeFilter(filters.FilterSet):
    class Meta:
        model = ServerAttribute
        fields = ['property_att__id', 'property_att__prefix', 'value']


class StoreFilter(filters.FilterSet):
    class Meta:
        model = Store
        fields = ['project__id']
