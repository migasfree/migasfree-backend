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
            'status', 'hardware'
        )


class ErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Error
        fields = (
            'id', 'computer', 'project',
            'description', 'checked', 'created_at'
        )


class FaultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Fault
        fields = (
            'id', 'computer', 'project',
            'fault_definition', 'result', 'checked', 'created_at'
        )


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Package
        fields = (
            'id', 'fullname', 'name', 'version',
            'architecture', 'project'
        )


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Notification
        fields = ('id', 'created_at', 'message', 'checked')


class SynchronizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Synchronization
        fields = (
            'id', 'created_at', 'computer', 'user', 'project',
            'start_date', 'consumer', 'pms_status_ok'
        )


class MigrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Migration
        fields = ('id', 'created_at', 'computer', 'project')
