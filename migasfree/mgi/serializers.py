# Copyright (c) 2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2026 Alberto Gacías <alberto@migasfree.org>
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

from ..core.models import ServerAttribute
from .models import Build, Config, Flavour, Release


class ConfigSerializer(serializers.ModelSerializer):
    dockerfile = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Config
        fields = (
            'id',
            'project',
            'template_id',
            'build_type',
            'base_os',
            'partition',
            'provision_script',
            'image_format',
            'config',
            'dockerfile',
        )
        read_only_fields = ('id',)


class FlavourSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=ServerAttribute.objects.filter(property_att__sort='server'), required=False
    )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = ', '.join(str(tag) for tag in instance.tags.all())
        return representation

    class Meta:
        model = Flavour
        fields = '__all__'


class ReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Release
        fields = '__all__'
        read_only_fields = ('created_at',)


class BuildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Build
        fields = '__all__'
