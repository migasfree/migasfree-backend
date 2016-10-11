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

# from django.utils.translation import ugettext_lazy as _

from .models import (
    Package, Error, Notification, FaultDefinition, Fault,
    Computer, Migration, StatusLog, Synchronization,
)


class ComputerFilter(filters.FilterSet):
    platform = filters.CharFilter(name='project__platform__id')
    created_at = filters.DateFilter(name='created_at', lookup_type='gte')
    software_inventory = filters.CharFilter(
        name='software_inventory__fullname', lookup_type='contains'
    )
    sync_attributes = filters.CharFilter(
        name='sync_attributes__value', lookup_type='contains'
    )
    mac_address = filters.CharFilter(
        name='mac_address', lookup_type='icontains'
    )

    class Meta:
        model = Computer
        fields = ['project__id', 'status', 'name']


class ErrorFilter(filters.FilterSet):
    created_at = filters.DateFilter(name='created_at', lookup_type='gte')
    created_at__lt = filters.DateFilter(name='created_at', lookup_expr='lt')

    class Meta:
        model = Error
        fields = ['project__id', 'checked', 'computer__id']


class FaultDefinitionFilter(filters.FilterSet):
    class Meta:
        model = FaultDefinition
        fields = [
            'included_attributes__id', 'excluded_attributes__id', 'enabled'
        ]


class FaultFilter(filters.FilterSet):
    created_at = filters.DateFilter(name='created_at', lookup_type='gte')
    created_at__lt = filters.DateFilter(name='created_at', lookup_expr='lt')

    """
    # TODO override filter_queryset (http://www.django-rest-framework.org/api-guide/filtering/)
    user = filters.ChoiceFilter(
        choices=Fault.USER_FILTER_CHOICES,
        label=_('User'),
        action=filter_by_user
    )

    def filter_by_user(qs, user):
        me = request.user.id  # FIXME no access to request.user :(
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
            'project__id', 'checked', 'fault_definition__id', 'computer__id'
        ]


class MigrationFilter(filters.FilterSet):
    created_at = filters.DateFilter(name='created_at', lookup_type='gte')
    created_at__lt = filters.DateFilter(name='created_at', lookup_expr='lt')

    class Meta:
        model = Migration
        fields = ['project__id', 'computer__id']


class NotificationFilter(filters.FilterSet):
    created_at = filters.DateFilter(name='created_at', lookup_type='gte')

    class Meta:
        model = Notification
        fields = ['checked']


class PackageFilter(filters.FilterSet):
    fullname = filters.CharFilter(name='fullname', lookup_type='contains')
    project = filters.CharFilter(name='project__id', lookup_type='exact')

    class Meta:
        model = Package


class StatusLogFilter(filters.FilterSet):
    created_at = filters.DateFilter(name='created_at', lookup_type='gte')
    created_at__lt = filters.DateFilter(name='created_at', lookup_expr='lt')

    class Meta:
        model = StatusLog
        fields = ['computer__id']


class SynchronizationFilter(filters.FilterSet):
    created_at = filters.DateFilter(name='created_at', lookup_type='gte')
    created_at__lt = filters.DateFilter(name='created_at', lookup_expr='lt')

    class Meta:
        model = Synchronization
        fields = ['project__id', 'computer__id']
