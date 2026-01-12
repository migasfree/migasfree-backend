# Copyright (c) 2015-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2021 Alberto Gacías <alberto@migasfree.org>
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

from ..client.serializers import ComputerInfoSerializer
from . import models


class NodeInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Node
        fields = ('id', 'name')


class NodeOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Node
        fields = (
            'id',
            'parent',
            'level',
            'width',
            'name',
            'class_name',
            'enabled',
            'claimed',
            'description',
            'vendor',
            'product',
            'version',
            'serial',
            'bus_info',
            'physid',
            'slot',
            'size',
            'capacity',
            'clock',
            'dev',
        )


class NodeSerializer(serializers.ModelSerializer):
    computer = ComputerInfoSerializer(many=False, read_only=True)

    class Meta:
        model = models.Node
        fields = '__all__'


class CapabilityInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Capability
        fields = ('id', 'name', 'description')


class ConfigurationInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Configuration
        fields = ('id', 'name', 'value')


class LogicalNameInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LogicalName
        fields = ('id', 'name')
