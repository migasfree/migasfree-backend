# Copyright (c) 2015-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2026 Alberto Gacías <alberto@migasfree.org>
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

"""
Platform and Project serializers.
"""

from rest_framework import serializers

from ..models import Platform, Project
from ..validators import validate_project_pms


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platform
        fields = '__all__'


class ProjectInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'name', 'slug', 'pms', 'architecture')


class ProjectNestedInfoSerializer(serializers.ModelSerializer):
    platform = PlatformSerializer(many=False, read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'name', 'slug', 'platform')


class ProjectSerializer(serializers.ModelSerializer):
    platform = PlatformSerializer(many=False, read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'name', 'slug', 'pms', 'architecture', 'auto_register_computers', 'base_os', 'platform')


class ProjectWriteSerializer(serializers.ModelSerializer):
    def init(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pms'].validators.append(validate_project_pms)

    def to_representation(self, obj):
        representation = super().to_representation(obj)

        representation['platform'] = PlatformSerializer(obj.platform).data

        return representation

    class Meta:
        model = Project
        fields = ('id', 'name', 'pms', 'architecture', 'auto_register_computers', 'base_os', 'platform')
