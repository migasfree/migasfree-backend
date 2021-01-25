# -*- coding: utf-8 -*-

# Copyright (c) 2017-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2017-2021 Alberto Gacías <alberto@migasfree.org>
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

from django.http import QueryDict
from rest_framework import serializers

from ..core.serializers import (
    AttributeInfoSerializer, ProjectInfoSerializer
)
from ..utils import to_list
from . import models


class LevelSerializer(serializers.Serializer):
    def to_representation(self, obj):
        return {
            'id': obj,
            'name': dict(models.Application.LEVELS)[obj]
        }


class CategorySerializer(serializers.Serializer):
    def to_representation(self, obj):
        return {
            'id': obj,
            'name': dict(models.Application.CATEGORIES)[obj]
        }


class PackagesByProjectWriteSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        """
        :param data: {
            'project': 17,
            'application': 1,
            'packages_to_install': ['one', 'two']
        }
        :return: PackagesByProject object
        """
        if 'packages_to_install' in data:
            data['packages_to_install'] = '\n'.join(data.get('packages_to_install', []))

        return super().to_internal_value(data)

    class Meta:
        model = models.PackagesByProject
        fields = '__all__'


class PackagesByProjectSerializer(serializers.ModelSerializer):
    project = ProjectInfoSerializer(many=False, read_only=True)

    def to_representation(self, obj):
        return {
            'project': {
                'id': obj.project.id,
                'name': obj.project.name
            },
            'packages_to_install': to_list(obj.packages_to_install)
        }

    class Meta:
        model = models.PackagesByProject
        fields = '__all__'


class ApplicationInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Application
        fields = ['id', 'name']


class ApplicationWriteSerializer(serializers.ModelSerializer):
    icon = serializers.ImageField(required=False)

    def to_internal_value(self, data):
        if isinstance(data, QueryDict):
            data = dict(data.lists())

        if 'name' in data and isinstance(data['name'], list):
            data['name'] = data['name'][0]

        if 'score' in data and isinstance(data['score'], list):
            data['score'] = int(data['score'][0])

        if 'description' in data and isinstance(data['description'], list):
            data['description'] = data['description'][0]

        if 'level' in data and isinstance(data['level'], list):
            data['level'] = data['level'][0]

        if 'category' in data and isinstance(data['category'], list):
            data['category'] = int(data['category'][0])

        if 'available_for_attributes' in data and isinstance(data['available_for_attributes'], list):
            try:
                data['available_for_attributes'] = list(map(int, data['available_for_attributes']))
            except ValueError:
                data['available_for_attributes'] = []

        if 'icon' in data and isinstance(data['icon'], list):
            data['icon'] = data['icon'][0]

        return super().to_internal_value(data)

    class Meta:
        model = models.Application
        fields = '__all__'


class ApplicationSerializer(serializers.ModelSerializer):
    level = LevelSerializer(many=False, read_only=True)
    category = CategorySerializer(many=False, read_only=True)
    packages_by_project = PackagesByProjectSerializer(many=True, read_only=True)
    available_for_attributes = AttributeInfoSerializer(many=True, read_only=True)

    class Meta:
        model = models.Application
        fields = '__all__'


class PolicyInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Policy
        fields = ['id', 'name']


class PolicyWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Policy
        fields = '__all__'


class PolicySerializer(serializers.ModelSerializer):
    included_attributes = AttributeInfoSerializer(many=True, read_only=True)
    excluded_attributes = AttributeInfoSerializer(many=True, read_only=True)

    class Meta:
        model = models.Policy
        fields = '__all__'


class PolicyGroupWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PolicyGroup
        fields = '__all__'


class PolicyGroupSerializer(serializers.ModelSerializer):
    policy = PolicyInfoSerializer(many=False, read_only=True)
    applications = ApplicationInfoSerializer(many=True, read_only=True)
    included_attributes = AttributeInfoSerializer(many=True, read_only=True)
    excluded_attributes = AttributeInfoSerializer(many=True, read_only=True)

    class Meta:
        model = models.PolicyGroup
        fields = '__all__'
