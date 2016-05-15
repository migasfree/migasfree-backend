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

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

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
            'id', 'uuid', 'name', 'project', 'ip_address',
            'software_inventory', 'software_history', 'tags',
            'status', 'product', 'machine', 'cpu', 'ram',
            'storage', 'disks', 'mac_address'
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


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Package
        fields = '__all__'


class SynchronizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Synchronization
        fields = '__all__'
