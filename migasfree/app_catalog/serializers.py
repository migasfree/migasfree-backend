# -*- coding: utf-8 -*-

# Copyright (c) 2017 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2017 Alberto Gacías <alberto@migasfree.org>
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

from migasfree.core.serializers import ProjectInfoSerializer
from migasfree.utils import to_list
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


class ApplicationSerializer(serializers.ModelSerializer):
    level = LevelSerializer(many=False, read_only=True)
    category = CategorySerializer(many=False, read_only=True)
    packages_by_project = PackagesByProjectSerializer(many=True, read_only=True)

    class Meta:
        model = models.Application
        fields = '__all__'
