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

from rest_framework import serializers

from ..core.serializers import ClientAttributeSerializer, ProjectInfoSerializer
from . import models


class ComputerSerializer(serializers.ModelSerializer):
    software_inventory = serializers.HyperlinkedIdentityField(
        view_name='computer-software/inventory'
    )
    software_history = serializers.HyperlinkedIdentityField(
        view_name='computer-software/history'
    )

    class Meta:
        model = models.Computer
        fields = (
            'id', 'uuid', 'name', 'fqdn', 'project',
            'ip_address', 'forwarded_ip_address', 'tags',
            'software_inventory', 'software_history',
            'status', 'product', 'machine', 'cpu', 'ram',
            'storage', 'disks', 'mac_address', 'comment'
        )


class ErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Error
        fields = '__all__'


class FaultDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FaultDefinition
        fields = '__all__'


class FaultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Fault
        fields = '__all__'


class MigrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Migration
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Notification
        fields = '__all__'


class PackageHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PackageHistory
        fields = '__all__'


class StatusLogSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return obj.get_status_display()

    class Meta:
        model = models.StatusLog
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = '__all__'


class SynchronizationSerializer(serializers.ModelSerializer):
    project = ProjectInfoSerializer(many=False, read_only=True)
    user = UserSerializer(many=False, read_only=True)

    class Meta:
        model = models.Synchronization
        fields = '__all__'


class SynchronizationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Synchronization
        fields = '__all__'


class ComputerSyncSerializer(serializers.ModelSerializer):
    sync_user = UserSerializer(many=False, read_only=True)
    sync_attributes = ClientAttributeSerializer(many=True, read_only=True)

    class Meta:
        model = models.Computer
        fields = ('sync_start_date', 'sync_end_date', 'sync_user', 'sync_attributes')
