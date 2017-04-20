# -*- coding: utf-8 -*-

# Copyright (c) 2015-2017 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2017 Alberto Gacías <alberto@migasfree.org>
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
    created_at = filters.DateFilter(name='created_at', lookup_expr=['gte'])
    software_inventory = filters.CharFilter(
        name='software_inventory__fullname', lookup_expr=['contains']
    )
    sync_attributes = filters.CharFilter(
        name='sync_attributes__value', lookup_expr=['contains']
    )
    mac_address = filters.CharFilter(
        name='mac_address', lookup_expr=['icontains']
    )

    class Meta:
        model = Computer
        fields = [
            'id', 'project__id', 'status', 'name',
            'uuid', 'sync_attributes__id', 'tags__id',
        ]


class ErrorFilter(filters.FilterSet):
    created_at = filters.DateFilter(name='created_at', lookup_expr=['gte'])
    created_at__lt = filters.DateFilter(name='created_at', lookup_expr=['lt'])

    class Meta:
        model = Error
        fields = ['id', 'project__id', 'checked', 'computer__id']


class FaultDefinitionFilter(filters.FilterSet):
    class Meta:
        model = FaultDefinition
        fields = [
            'id', 'enabled',
            'included_attributes__id', 'excluded_attributes__id'
        ]


class FaultFilter(filters.FilterSet):
    created_at = filters.DateFilter(name='created_at', lookup_expr=['gte'])
    created_at__lt = filters.DateFilter(name='created_at', lookup_expr=['lt'])

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
            'id', 'project__id', 'checked',
            'fault_definition__id', 'computer__id'
        ]


class MigrationFilter(filters.FilterSet):
    created_at = filters.DateFilter(name='created_at', lookup_expr=['gte'])
    created_at__lt = filters.DateFilter(name='created_at', lookup_expr=['lt'])

    class Meta:
        model = Migration
        fields = ['id', 'project__id', 'computer__id']


class NotificationFilter(filters.FilterSet):
    created_at = filters.DateFilter(name='created_at', lookup_expr=['gte'])

    class Meta:
        model = Notification
        fields = ['id', 'checked']


class PackageFilter(filters.FilterSet):
    fullname = filters.CharFilter(name='fullname', lookup_expr=['contains'])
    project = filters.CharFilter(name='project__id', lookup_expr=['exact'])

    class Meta:
        model = Package


class StatusLogFilter(filters.FilterSet):
    created_at = filters.DateFilter(name='created_at', lookup_expr=['gte'])
    created_at__lt = filters.DateFilter(name='created_at', lookup_expr=['lt'])

    class Meta:
        model = StatusLog
        fields = ['id', 'computer__id']


class SynchronizationFilter(filters.FilterSet):
    created_at = filters.DateFilter(name='created_at', lookup_expr=['gte'])
    created_at__lt = filters.DateFilter(name='created_at', lookup_expr=['lt'])

    class Meta:
        model = Synchronization
        fields = ['id', 'project__id', 'computer__id']
