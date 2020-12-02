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

from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters

from ..hardware.models import Node

from .models import (
    PackageHistory, Error, Notification, FaultDefinition, Fault,
    Computer, Migration, StatusLog, Synchronization,
)


class ComputerFilter(filters.FilterSet):
    platform = filters.CharFilter(field_name='project__platform__id')
    created_at__gte = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at__lt = filters.DateFilter(field_name='created_at', lookup_expr='lt')
    sync_attributes = filters.CharFilter(
        field_name='sync_attributes__value', lookup_expr='contains'
    )
    mac_address = filters.CharFilter(
        field_name='mac_address', lookup_expr='icontains'
    )
    has_software_inventory = filters.BooleanFilter(
        method='filter_has_software_inventory',
        label='has software inventory'
    )
    architecture = filters.NumberFilter(
        method='filter_architecture',
        label='architecture'
    )
    product_system = filters.ChoiceFilter(
        method='filter_product_system',
        label='product system',
        choices=(
            ('docker', 'docker'),
            ('virtual', 'virtual'),
            ('laptop', 'laptop'),
            ('desktop', 'desktop'),
        )
    )

    def filter_has_software_inventory(self, qs, name, value):
        if value:
            return qs.exclude(packagehistory=None)

        return qs.filter(packagehistory=None)

    def filter_architecture(self, qs, name, value):
        return qs.filter(
            Q(node__class_name='processor', node__width=value) |
            Q(node__class_name='system', node__width=value)
        ).distinct()

    def filter_product_system(self, qs, name, value):
        if value == 'docker':
            return qs.filter(
                node__name='network',
                node__class_name='network',
                node__description='Ethernet interface',
                node__serial__istartswith='02:42:AC'
            )

        if value == 'virtual':
            return qs.filter(
                node__parent_id__isnull=True,
                node__vendor__in=list(Node.VIRTUAL_MACHINES.keys())
            )

        if value == 'laptop':
            return qs.filter(
                node__class_name='system',
                node__configuration__name='chassis',
                node__configuration__value='notebook'
            )

        if value == 'desktop':
            return qs.filter(
                node__class_name='system',
                node__configuration__name='chassis'
            ).exclude(
                node__configuration__value='notebook'
            )

        return qs

    class Meta:
        model = Computer
        fields = {
            'id': ['exact'],
            'project__id': ['exact'],
            'status': ['exact', 'in'],
            'name': ['exact', 'icontains'],
            'uuid': ['exact'],
            'sync_attributes__id': ['exact'],
            'tags__id': ['exact'],
            'machine': ['exact'],
            'sync_user__name': ['exact', 'icontains'],
            'sync_end_date': ['lt', 'gte', 'isnull'],
            'product': ['exact', 'icontains'],
        }


class ErrorFilter(filters.FilterSet):
    created_at__gte = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at__lt = filters.DateFilter(field_name='created_at', lookup_expr='lt')

    class Meta:
        model = Error
        fields = {
            'id': ['exact'],
            'project__id': ['exact'],
            'project__platform__id': ['exact'],
            'checked': ['exact'],
            'computer__id': ['exact'],
            'computer__name': ['icontains'],
            'computer__status': ['exact', 'in'],
            'description': ['icontains'],
        }


class FaultDefinitionFilter(filters.FilterSet):
    class Meta:
        model = FaultDefinition
        fields = [
            'id', 'name', 'enabled',
            'included_attributes__id', 'excluded_attributes__id'
        ]


class FaultFilter(filters.FilterSet):
    created_at__gte = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at__lt = filters.DateFilter(field_name='created_at', lookup_expr='lt')

    user = filters.ChoiceFilter(
        choices=Fault.USER_FILTER_CHOICES,
        label=_('User'),
        method='filter_by_user'
    )

    def filter_by_user(self, qs, name, value):
        me = self.request.user.id
        if value == 'me':
            return qs.filter(
                Q(fault_definition__users__id=me)
                | Q(fault_definition__users=None)
            )
        elif value == 'only_me':
            return qs.filter(fault_definition__users__id=me)
        elif value == 'others':
            return qs.exclude(
                fault_definition__users__id=me
            ).exclude(fault_definition__users=None)
        elif value == 'unassigned':
            return qs.filter(Q(fault_definition__users=None))

    class Meta:
        model = Fault
        fields = {
            'id': ['exact'],
            'project__id': ['exact'],
            'project__platform__id': ['exact'],
            'checked': ['exact'],
            'computer__id': ['exact'],
            'computer__name': ['icontains'],
            'fault_definition_id': ['exact'],
            'result': ['icontains'],
        }


class MigrationFilter(filters.FilterSet):
    created_at__gte = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at__lt = filters.DateFilter(field_name='created_at', lookup_expr='lt')

    class Meta:
        model = Migration
        fields = ['id', 'project__id', 'computer__id']


class NotificationFilter(filters.FilterSet):
    created_at__gte = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at__lt = filters.DateFilter(field_name='created_at', lookup_expr='lt')

    class Meta:
        model = Notification
        fields = ['id', 'checked']


class PackageHistoryFilter(filters.FilterSet):
    computer = filters.CharFilter(field_name='computer__name', lookup_expr='contains')
    package = filters.CharFilter(field_name='package__fullname', lookup_expr='contains')

    class Meta:
        model = PackageHistory
        fields = '__all__'


class StatusLogFilter(filters.FilterSet):
    created_at__gte = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at__lt = filters.DateFilter(field_name='created_at', lookup_expr='lt')

    class Meta:
        model = StatusLog
        fields = ['id', 'computer__id']


class SynchronizationFilter(filters.FilterSet):
    created_at__gte = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at__lt = filters.DateFilter(field_name='created_at', lookup_expr='lt')

    start_date__gte = filters.DateFilter(field_name='start_date', lookup_expr='gte')
    start_date__lt = filters.DateFilter(field_name='start_date', lookup_expr='lt')

    class Meta:
        model = Synchronization
        fields = {
            'id': ['exact'],
            'project__id': ['exact'],
            'project__platform__id': ['exact'],
            'computer__id': ['exact'],
            'computer__name': ['icontains'],
            'pms_status_ok': ['exact'],
            'consumer': ['icontains']
        }
