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

from rest_framework import serializers

from ..core.serializers import (
    ClientAttributeSerializer, ProjectInfoSerializer,
    AttributeInfoSerializer, PackageInfoSerializer,
    ProjectNestedInfoSerializer, UserProfileInfoSerializer,
)
from ..device.serializers import LogicalInfoSerializer
from . import models


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ('id', 'name')


class ComputerInfoSerializer(serializers.ModelSerializer):
    summary = serializers.SerializerMethodField()

    def get_summary(self, obj):
        return obj.get_summary()

    class Meta:
        model = models.Computer
        fields = ('id', '__str__', 'status', 'summary')


class ComputerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Computer
        fields = (
            'id', 'uuid', 'name', 'project',
            'ip_address', 'forwarded_ip_address',
        )


class ComputerWriteSerializer(serializers.ModelSerializer):
    def is_valid(self, raise_exception=False):
        data = self.get_initial()
        if data.get('tags') and data.get('tags')[0] == '':
            self.instance.tags.clear()
            del self.fields['tags']

        return super().is_valid(raise_exception)

    class Meta:
        model = models.Computer
        fields = (
            'name', 'last_hardware_capture',
            'status', 'comment', 'tags',
            'default_logical_device', 'project',
        )


class ComputerSerializer(serializers.ModelSerializer):
    project = ProjectNestedInfoSerializer(many=False, read_only=True)
    software_inventory = serializers.HyperlinkedIdentityField(
        view_name='computer-software_inventory'
    )
    software_history = serializers.HyperlinkedIdentityField(
        view_name='computer-software_history'
    )
    tags = AttributeInfoSerializer(many=True, read_only=True)
    sync_user = UserInfoSerializer(many=False, read_only=True)
    architecture = serializers.SerializerMethodField()
    product_system = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()

    def get_architecture(self, obj):
        return obj.get_architecture()

    def get_product_system(self, obj):
        return obj.product_system()

    def get_summary(self, obj):
        return obj.get_summary()

    class Meta:
        model = models.Computer
        fields = (
            'id', 'uuid', 'name', 'fqdn', 'project',
            'ip_address', 'forwarded_ip_address', 'tags',
            'software_inventory', 'software_history', 'has_software_inventory',
            'status', 'product', 'machine', 'product_system',
            'cpu', 'architecture', 'ram',
            'storage', 'disks', 'mac_address', 'comment',
            'created_at', 'last_hardware_capture',
            'sync_user', 'sync_end_date',
            '__str__', 'summary'
        )


class ComputerDevicesSerializer(serializers.ModelSerializer):
    assigned_logical_devices_to_cid = LogicalInfoSerializer(many=True, read_only=True)
    inflicted_logical_devices = LogicalInfoSerializer(many=True, read_only=True)

    class Meta:
        model = models.Computer
        fields = (
            'default_logical_device',
            'assigned_logical_devices_to_cid',
            'inflicted_logical_devices'
        )


class ErrorSerializer(serializers.ModelSerializer):
    project = ProjectInfoSerializer(many=False, read_only=True)
    computer = ComputerInfoSerializer(many=False, read_only=True)

    class Meta:
        model = models.Error
        fields = (
            'id', '__str__',
            'project', 'computer',
            'created_at', 'checked', 'description'
        )


class ErrorWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Error
        fields = ('checked',)


class ErrorSafeWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Error
        fields = '__all__'


class FaultDefinitionInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FaultDefinition
        fields = ('id', 'name')


class FaultDefinitionSerializer(serializers.ModelSerializer):
    included_attributes = AttributeInfoSerializer(many=True, read_only=True)
    excluded_attributes = AttributeInfoSerializer(many=True, read_only=True)
    users = UserProfileInfoSerializer(many=True, read_only=True)

    class Meta:
        model = models.FaultDefinition
        fields = '__all__'


class FaultDefinitionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FaultDefinition
        fields = '__all__'


class FaultSerializer(serializers.ModelSerializer):
    project = ProjectInfoSerializer(many=False, read_only=True)
    computer = ComputerInfoSerializer(many=False, read_only=True)
    fault_definition = FaultDefinitionInfoSerializer(many=False, read_only=True)

    class Meta:
        model = models.Fault
        fields = (
            'id', '__str__',
            'project', 'computer', 'fault_definition',
            'created_at', 'checked', 'result'
        )


class FaultWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Fault
        fields = ('checked',)


class MigrationSerializer(serializers.ModelSerializer):
    project = ProjectInfoSerializer(many=False, read_only=True)
    computer = ComputerInfoSerializer(many=False, read_only=True)

    class Meta:
        model = models.Migration
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Notification
        fields = '__all__'


class NotificationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Notification
        fields = ('checked',)


class PackageHistorySerializer(serializers.ModelSerializer):
    package = PackageInfoSerializer(many=False, read_only=True)

    class Meta:
        model = models.PackageHistory
        fields = '__all__'


class StatusLogSerializer(serializers.ModelSerializer):
    computer = ComputerInfoSerializer(many=False, read_only=True)
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
    computer = ComputerInfoSerializer(many=False, read_only=True)

    class Meta:
        model = models.Synchronization
        fields = '__all__'


class SynchronizationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Synchronization
        fields = ('computer', 'start_date', 'consumer', 'pms_status_ok')


class ComputerSyncSerializer(serializers.ModelSerializer):
    sync_user = UserSerializer(many=False, read_only=True)
    sync_attributes = ClientAttributeSerializer(many=True, read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        context = kwargs.get('context', None)
        if context:
            request = kwargs['context']['request']
            self.sync_attributes = ClientAttributeSerializer(
                many=True, read_only=True, context={'request': request}
            )

    class Meta:
        model = models.Computer
        fields = ('sync_start_date', 'sync_end_date', 'sync_user', 'sync_attributes')
