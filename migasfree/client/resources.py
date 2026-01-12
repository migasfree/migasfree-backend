# Copyright (c) 2019-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2019-2026 Alberto Gacías <alberto@migasfree.org>
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

from import_export import resources

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


class ComputerResource(resources.ModelResource):
    def dehydrate_project(self, computer):
        return computer.project.name

    def dehydrate_sync_user(self, computer):
        return computer.sync_user

    class Meta:
        model = Computer
        exclude = (
            'software_history',
            'software_inventory',
            'sync_attributes',
            'default_logical_device',
        )


class UserResource(resources.ModelResource):
    class Meta:
        model = User


class ErrorResource(resources.ModelResource):
    class Meta:
        model = Error


class FaultDefinitionResource(resources.ModelResource):
    class Meta:
        model = FaultDefinition


class FaultResource(resources.ModelResource):
    class Meta:
        model = Fault


class MigrationResource(resources.ModelResource):
    class Meta:
        model = Migration


class StatusLogResource(resources.ModelResource):
    class Meta:
        model = StatusLog


class SynchronizationResource(resources.ModelResource):
    class Meta:
        model = Synchronization


class NotificationResource(resources.ModelResource):
    class Meta:
        model = Notification


class PackageHistoryResource(resources.ModelResource):
    class Meta:
        model = PackageHistory
        fields = ('id', 'computer', 'computer__name', 'package', 'package__fullname', 'install_date', 'uninstall_date')
        export_order = (
            'id',
            'computer',
            'computer__name',
            'package',
            'package__fullname',
            'install_date',
            'uninstall_date',
        )
