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
        method='filter_has_software_inventory'
    )

    def filter_has_software_inventory(self, qs, name, value):
        if value:
            return qs.exclude(packagehistory=None)

        return qs.filter(packagehistory=None)

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
    created_at = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at__lt = filters.DateFilter(field_name='created_at', lookup_expr='lt')

    class Meta:
        model = Error
        fields = ['id', 'project__id', 'checked', 'computer__id']


class FaultDefinitionFilter(filters.FilterSet):
    class Meta:
        model = FaultDefinition
        fields = [
            'id', 'name', 'enabled',
            'included_attributes__id', 'excluded_attributes__id'
        ]


class FaultFilter(filters.FilterSet):
    created_at = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at__lt = filters.DateFilter(field_name='created_at', lookup_expr='lt')

    """
    # TODO override filter_queryset (http://www.django-rest-framework.org/api-guide/filtering/)
    user = filters.ChoiceFilter(
        choices=Fault.USER_FILTER_CHOICES,
        label=_('User'),
        action=filter_by_user
    )

    def filter_by_user(self, qs, user):
        me = self.request.user.id  # TODO test it
        if user == 'me':
            return qs.filter(
                Q(fault_definition__users__id=me)
                | Q(fault_definition__users=None)
            )
        elif user == 'only_me':
            return qs.filter(fault_definition__users__id=me)
        elif user == 'others':
            return qs.exclude(
                fault_definition__users__id=me
            ).exclude(fault_definition__users=None)
        elif user == 'unassigned':
            return qs.filter(Q(fault_definition__users=None))
    """

    class Meta:
        model = Fault
        fields = [
            'id', 'project__id', 'checked',
            'fault_definition__id', 'computer__id'
        ]


class MigrationFilter(filters.FilterSet):
    created_at = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at__lt = filters.DateFilter(field_name='created_at', lookup_expr='lt')

    class Meta:
        model = Migration
        fields = ['id', 'project__id', 'computer__id']


class NotificationFilter(filters.FilterSet):
    created_at = filters.DateFilter(field_name='created_at', lookup_expr='gte')

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
    created_at = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at__lt = filters.DateFilter(field_name='created_at', lookup_expr='lt')

    class Meta:
        model = StatusLog
        fields = ['id', 'computer__id']


class SynchronizationFilter(filters.FilterSet):
    created_at = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at__lt = filters.DateFilter(field_name='created_at', lookup_expr='lt')

    class Meta:
        model = Synchronization
        fields = ['id', 'project__id', 'computer__id']
