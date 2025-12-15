# Copyright (c) 2015-2025 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2025 Alberto Gacías <alberto@migasfree.org>
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
    Computer,
    Error,
    Fault,
    FaultDefinition,
    Migration,
    Notification,
    PackageHistory,
    StatusLog,
    Synchronization,
    User,
)


class ComputerFilter(filters.FilterSet):
    platform = filters.CharFilter(field_name='project__platform__id')
    created_at__gte = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at__lt = filters.DateTimeFilter(field_name='created_at', lookup_expr='lt')
    sync_attributes = filters.CharFilter(field_name='sync_attributes__value', lookup_expr='contains')
    mac_address = filters.CharFilter(field_name='mac_address', lookup_expr='icontains')
    has_software_inventory = filters.BooleanFilter(
        method='filter_has_software_inventory', label='has software inventory'
    )
    architecture = filters.NumberFilter(method='filter_architecture', label='architecture')
    product_system = filters.ChoiceFilter(
        method='filter_product_system',
        label='product system',
        choices=(
            ('docker', 'docker'),
            ('virtual', 'virtual'),
            ('laptop', 'laptop'),
            ('desktop', 'desktop'),
        ),
    )
    installed_package = filters.NumberFilter(method='filter_installed_package', label='installed_package')
    serial = filters.CharFilter(method='filter_serial', label='serial')

    def filter_has_software_inventory(self, qs, name, value):
        if value:
            return qs.exclude(packagehistory=None)

        return qs.filter(packagehistory=None)

    def filter_architecture(self, qs, name, value):
        return qs.filter(
            Q(node__class_name='processor', node__width=value) | Q(node__class_name='system', node__width=value)
        ).distinct()

    def filter_product_system(self, qs, name, value):
        if value == 'docker':
            return qs.filter(
                node__name='network',
                node__class_name='network',
                node__description='Ethernet interface',
                node__serial__istartswith='02:42:AC',
            )

        if value == 'virtual':
            return qs.filter(node__parent_id__isnull=True, node__vendor__in=list(Node.VIRTUAL_MACHINES.keys()))

        if value == 'laptop':
            return qs.filter(
                node__class_name='system', node__configuration__name='chassis', node__configuration__value='notebook'
            )

        if value == 'desktop':
            return qs.filter(node__class_name='system', node__configuration__name='chassis').exclude(
                node__configuration__value='notebook'
            )

        return qs

    def filter_installed_package(self, qs, name, value):
        return qs.filter(packagehistory__package__id=value, packagehistory__uninstall_date__isnull=True)

    def filter_serial(self, qs, name, value):
        return qs.filter(node__serial__icontains=value)

    class Meta:
        model = Computer
        fields = {
            'id': ['exact', 'in'],
            'project__id': ['exact'],
            'status': ['exact', 'in'],
            'name': ['exact', 'icontains'],
            'uuid': ['exact', 'icontains'],
            'sync_attributes__id': ['exact', 'in'],
            'tags__id': ['exact', 'in'],
            'machine': ['exact'],
            'sync_user__id': ['exact'],
            'sync_user__name': ['exact', 'icontains'],
            'sync_end_date': ['lt', 'gte', 'isnull'],
            'product': ['exact', 'icontains'],
            'default_logical_device__id': ['exact'],
        }


class ErrorFilter(filters.FilterSet):
    created_at__gte = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at__lt = filters.DateTimeFilter(field_name='created_at', lookup_expr='lt')

    class Meta:
        model = Error
        fields = {
            'id': ['exact', 'in'],
            'project__id': ['exact'],
            'project__platform__id': ['exact'],
            'checked': ['exact'],
            'computer__id': ['exact'],
            'computer__name': ['exact', 'icontains'],
            'computer__status': ['exact', 'in'],
            'description': ['icontains'],
        }


class FaultDefinitionFilter(filters.FilterSet):
    class Meta:
        model = FaultDefinition
        fields = {
            'id': ['exact', 'in'],
            'name': ['exact', 'icontains'],
            'enabled': ['exact'],
            'language': ['exact'],
            'included_attributes__id': ['exact'],
            'excluded_attributes__id': ['exact'],
            'users__id': ['exact'],
        }


class FaultFilter(filters.FilterSet):
    created_at__gte = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at__lt = filters.DateTimeFilter(field_name='created_at', lookup_expr='lt')

    user = filters.ChoiceFilter(choices=Fault.USER_FILTER_CHOICES, label=_('User'), method='filter_by_user')

    def filter_by_user(self, qs, name, value):
        me = self.request.user.id
        if value == 'me':
            return qs.filter(Q(fault_definition__users__id=me) | Q(fault_definition__users=None))
        elif value == 'only_me':
            return qs.filter(fault_definition__users__id=me)
        elif value == 'others':
            return qs.exclude(fault_definition__users__id=me).exclude(fault_definition__users=None)
        elif value == 'unassigned':
            return qs.filter(Q(fault_definition__users=None))

    class Meta:
        model = Fault
        fields = {
            'id': ['exact', 'in'],
            'project__id': ['exact'],
            'project__platform__id': ['exact'],
            'checked': ['exact'],
            'computer__id': ['exact'],
            'computer__name': ['exact', 'icontains'],
            'fault_definition_id': ['exact'],
            'result': ['icontains'],
        }


class MigrationFilter(filters.FilterSet):
    created_at__gte = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at__lt = filters.DateTimeFilter(field_name='created_at', lookup_expr='lt')

    class Meta:
        model = Migration
        fields = {
            'id': ['exact', 'in'],
            'project__id': ['exact'],
            'project__platform__id': ['exact'],
            'computer__id': ['exact'],
            'computer__name': ['exact', 'icontains'],
        }


class NotificationFilter(filters.FilterSet):
    created_at__gte = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at__lt = filters.DateTimeFilter(field_name='created_at', lookup_expr='lt')

    class Meta:
        model = Notification
        fields = {
            'id': ['exact', 'in'],
            'checked': ['exact'],
            'message': ['exact', 'icontains'],
        }


class PackageHistoryFilter(filters.FilterSet):
    class Meta:
        model = PackageHistory
        fields = {
            'id': ['exact', 'in'],
            'computer__id': ['exact'],
            'computer__name': ['exact', 'icontains'],
            'package__id': ['exact'],
            'package__fullname': ['exact', 'icontains'],
            'package__project__id': ['exact'],
            'install_date': ['gte', 'lt'],
            'uninstall_date': ['gte', 'lt', 'isnull'],
        }


class StatusLogFilter(filters.FilterSet):
    created_at__gte = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at__lt = filters.DateTimeFilter(field_name='created_at', lookup_expr='lt')

    class Meta:
        model = StatusLog
        fields = {
            'id': ['exact', 'in'],
            'computer__id': ['exact'],
            'computer__name': ['exact', 'icontains'],
            'status': ['exact', 'in'],
        }


class SynchronizationFilter(filters.FilterSet):
    created_at__gte = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at__lt = filters.DateTimeFilter(field_name='created_at', lookup_expr='lt')

    start_date__gte = filters.DateTimeFilter(field_name='start_date', lookup_expr='gte')
    start_date__lt = filters.DateTimeFilter(field_name='start_date', lookup_expr='lt')

    class Meta:
        model = Synchronization
        fields = {
            'id': ['exact', 'in'],
            'project__id': ['exact'],
            'project__platform__id': ['exact'],
            'computer__id': ['exact'],
            'computer__name': ['exact', 'icontains'],
            'user__id': ['exact'],
            'user__name': ['exact', 'icontains'],
            'pms_status_ok': ['exact'],
            'consumer': ['exact', 'icontains'],
        }


class UserFilter(filters.FilterSet):
    class Meta:
        model = User
        fields = {
            'id': ['exact', 'in'],
            'name': ['exact', 'icontains'],
            'fullname': ['exact', 'icontains'],
        }
