# -*- coding: utf-8 -*-

# Copyright (c) 2015-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2021 Alberto Gacías <alberto@migasfree.org>
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
from django.contrib.auth.models import Permission, Group

from .models import (
    Deployment, Package, ClientAttribute, ServerAttribute, Attribute,
    Project, ScheduleDelay, Store, AttributeSet, Property, Platform,
    UserProfile, Domain, Scope, Schedule, PackageSet,
)


class AttributeSetFilter(filters.FilterSet):
    class Meta:
        model = AttributeSet
        fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains'],
            'enabled': ['exact'],
            'included_attributes__id': ['exact'],
            'excluded_attributes__id': ['exact'],
        }


class DeploymentFilter(filters.FilterSet):
    included_attributes = filters.CharFilter(
        field_name='included_attributes__value', lookup_expr='icontains'
    )
    excluded_attributes = filters.CharFilter(
        field_name='excluded_attributes__value', lookup_expr='icontains'
    )
    available_packages = filters.CharFilter(
        field_name='available_packages__name', lookup_expr='icontains'
    )

    class Meta:
        model = Deployment
        fields = {
            'id': ['exact', 'in'],
            'name': ['exact', 'icontains'],
            'project__id': ['exact'],
            'enabled': ['exact'],
            'source': ['exact'],
            'schedule': ['isnull'],
            'schedule__id': ['exact'],
            'domain__id': ['exact'],
            'available_packages__id': ['exact'],
            'available_package_sets__id': ['exact'],
            'included_attributes__id': ['exact'],
            'excluded_attributes__id': ['exact'],
        }


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
            'deployment': ['isnull'],
            'deployment__id': ['exact'],
            'store': ['isnull'],
            'store__id': ['exact'],
            'packageset__id': ['exact'],
        }


class PackageSetFilter(filters.FilterSet):
    class Meta:
        model = PackageSet
        fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains'],
            'project__id': ['exact'],
            'store__id': ['exact'],
            'packages__id': ['exact'],
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
            'id': ['exact', 'in'],
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
            'id': ['exact', 'in'],
            'property_att__id': ['exact'],
            'property_att__prefix': ['exact'],
            'value': ['exact', 'icontains'],
            'description': ['icontains'],
            'property_att__sort': ['exact'],
            'attributeset_included__id': ['exact'],
            'attributeset_excluded__id': ['exact'],
            'domain_included__id': ['exact'],
            'domain_excluded__id': ['exact'],
            'faultdefinition_included__id': ['exact'],
            'faultdefinition_excluded__id': ['exact'],
            'scope_included__id': ['exact'],
            'scope_excluded__id': ['exact'],
            'device__id': ['exact'],
            'logical__id': ['exact'],
            'deployment_included__id': ['exact'],
            'deployment_excluded__id': ['exact'],
            'application__id': ['exact'],
            'policy_included__id': ['exact'],
            'policy_excluded__id': ['exact'],
            'computer__id': ['exact'],
        }


class ClientAttributeFilter(filters.FilterSet):
    class Meta:
        model = ClientAttribute
        fields = {
            'id': ['exact', 'in'],
            'property_att__id': ['exact'],
            'property_att__prefix': ['exact'],
            'value': ['exact', 'icontains'],
            'description': ['icontains'],
            'property_att__sort': ['exact'],
            'attributeset_included__id': ['exact'],
            'attributeset_excluded__id': ['exact'],
            'domain_included__id': ['exact'],
            'domain_excluded__id': ['exact'],
            'faultdefinition_included__id': ['exact'],
            'faultdefinition_excluded__id': ['exact'],
            'scope_included__id': ['exact'],
            'scope_excluded__id': ['exact'],
            'device__id': ['exact'],
            'logical__id': ['exact'],
            'deployment_included__id': ['exact'],
            'deployment_excluded__id': ['exact'],
            'application__id': ['exact'],
            'policy_included__id': ['exact'],
            'policy_excluded__id': ['exact'],
            'computer__id': ['exact'],
        }


class ServerAttributeFilter(filters.FilterSet):
    class Meta:
        model = ServerAttribute
        fields = {
            'id': ['exact', 'in'],
            'property_att__id': ['exact'],
            'property_att__prefix': ['exact'],
            'value': ['exact', 'icontains'],
            'description': ['icontains'],
            'property_att__sort': ['exact'],
            'attributeset_included__id': ['exact'],
            'attributeset_excluded__id': ['exact'],
            'domain_included__id': ['exact'],
            'domain_excluded__id': ['exact'],
            'domain_tags__id': ['exact'],
            'faultdefinition_included__id': ['exact'],
            'faultdefinition_excluded__id': ['exact'],
            'scope_included__id': ['exact'],
            'scope_excluded__id': ['exact'],
            'device__id': ['exact'],
            'logical__id': ['exact'],
            'deployment_included__id': ['exact'],
            'deployment_excluded__id': ['exact'],
            'application__id': ['exact'],
            'policy_included__id': ['exact'],
            'policy_excluded__id': ['exact'],
            'computer__id': ['exact'],
            'tags__id': ['exact'],
        }


class ScheduleFilter(filters.FilterSet):
    class Meta:
        model = Schedule
        fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains'],
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


class UserProfileFilter(filters.FilterSet):
    class Meta:
        model = UserProfile
        fields = {
            'id': ['exact'],
            'username': ['exact', 'icontains'],
            'first_name': ['exact', 'icontains'],
            'last_name': ['exact', 'icontains'],
            'faultdefinition_users__id': ['exact'],
            'domains__id': ['exact'],
            'is_active': ['exact'],
            'is_staff': ['exact'],
            'is_superuser': ['exact'],
        }


class PermissionFilter(filters.FilterSet):
    class Meta:
        model = Permission
        fields = {
            'id': ['exact'],
            'name': ['icontains'],
        }


class GroupFilter(filters.FilterSet):
    class Meta:
        model = Group
        fields = {
            'id': ['exact'],
            'name': ['icontains'],
            'user__id': ['exact'],
        }


class DomainFilter(filters.FilterSet):
    class Meta:
        model = Domain
        fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains'],
        }


class ScopeFilter(filters.FilterSet):
    class Meta:
        model = Scope
        fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains'],
            'user': ['exact'],
            'user__id': ['exact'],
            'user__username': ['exact', 'icontains']
        }
