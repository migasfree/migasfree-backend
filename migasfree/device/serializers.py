# -*- coding: utf-8 -*-

# Copyright (c) 2016-2018 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2016-2018 Alberto Gacías <alberto@migasfree.org>
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

from migasfree.core.serializers import AttributeInfoSerializer, ProjectInfoSerializer

from ..utils import to_list
from . import models


class ConnectionInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Connection
        fields = ('id', 'name')


class ConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Connection
        fields = '__all__'


class ModelInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Model
        fields = ('id', 'name')


class DeviceInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Device
        fields = ('id', 'name')


class DeviceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Device
        fields = '__all__'


class DeviceSerializer(serializers.ModelSerializer):
    connection = ConnectionInfoSerializer(many=False, read_only=True)
    model = ModelInfoSerializer(many=False, read_only=True)
    available_for_attributes = AttributeInfoSerializer(many=True, read_only=True)

    class Meta:
        model = models.Device
        fields = '__all__'


class FeatureInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Feature
        fields = ('id', 'name')


class DriverWriteSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        if 'packages_to_install' in data:
            data['packages_to_install'] = '\n'.join(data.get('packages_to_install', []))

        return super(DriverWriteSerializer, self).to_internal_value(data)

    class Meta:
        model = models.Driver
        fields = '__all__'


class DriverSerializer(serializers.ModelSerializer):
    model = ModelInfoSerializer(many=False, read_only=True)
    project = ProjectInfoSerializer(many=False, read_only=True)
    feature = FeatureInfoSerializer(many=False, read_only=True)
    packages_to_install = serializers.SerializerMethodField()

    def get_packages_to_install(self, obj):
        return to_list(obj.packages_to_install)

    class Meta:
        model = models.Driver
        fields = '__all__'


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Feature
        fields = '__all__'


class LogicalInfoSerializer(serializers.ModelSerializer):
    device = DeviceInfoSerializer(many=False, read_only=True)
    feature = FeatureSerializer(many=False, read_only=True)

    class Meta:
        model = models.Logical
        fields = ('id', 'device', 'feature')


class LogicalSerializer(serializers.ModelSerializer):
    device = DeviceInfoSerializer(many=False, read_only=True)
    feature = FeatureSerializer(many=False, read_only=True)

    class Meta:
        model = models.Logical
        fields = '__all__'


class LogicalWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Logical
        fields = '__all__'


class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Manufacturer
        fields = '__all__'


class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Type
        fields = '__all__'


class ModelWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Model
        fields = '__all__'


class ModelSerializer(serializers.ModelSerializer):
    manufacturer = ManufacturerSerializer(many=False, read_only=True)
    connections = ConnectionInfoSerializer(many=True, read_only=True)
    device_type = TypeSerializer(many=False, read_only=True)

    class Meta:
        model = models.Model
        fields = '__all__'
