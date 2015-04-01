# -*- coding: utf-8 -*-

# Copyright (c) 2015 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015 Alberto Gacías <alberto@migasfree.org>
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

from django.utils.translation import ugettext_lazy as _

from .models import Package, Error, Notification, Fault, Computer


class PackageFilter(filters.FilterSet):
    class Meta:
        model = Package
        fields = {
            'project__id': ['exact'],
        }


class ErrorFilter(filters.FilterSet):
    created_at = filters.DateTimeFilter(name='created_at', lookup_type='gte')

    class Meta:
        model = Error
        fields = {
            'project__id': ['exact'],
            'checked': ['exact'],
            'created_at': ['lt', 'gte'],
        }


class NotificationFilter(filters.FilterSet):
    created_at = filters.DateTimeFilter(name='created_at', lookup_type='gte')

    class Meta:
        model = Notification
        fields = {
            'checked': ['exact'],
            'created_at': ['lt', 'gte'],
        }


class FaultFilter(filters.FilterSet):
    created_at = filters.DateTimeFilter(name='created_at', lookup_type='gte')

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
        fields = {
            'project__id': ['exact'],
            'checked': ['exact'],
            'created_at': ['lt', 'gte'],
            'fault_definition__id': ['exact'],
        }


class ComputerFilter(filters.FilterSet):
    class Meta:
        model = Computer
        fields = {
            'project__id': ['exact'],
        }
