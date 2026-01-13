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
Property and Attribute serializers.
"""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ..models import (
    Attribute,
    AttributeSet,
    ClientAttribute,
    ClientProperty,
    Property,
    ServerAttribute,
    ServerProperty,
    Singularity,
)
from .base import AttributeRepresentationMixin


class PropertyInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ('id', 'prefix', 'sort')


class PropertyWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = '__all__'


class PropertySerializer(serializers.ModelSerializer):
    language = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField)
    def get_language(self, obj):
        return obj.get_language_display()

    class Meta:
        model = Property
        fields = '__all__'


class AttributeSerializer(serializers.ModelSerializer):
    property_att = PropertyInfoSerializer(many=False, read_only=True)

    def get_total_computers(self, obj):
        if self.context.get('request'):
            return obj.total_computers(user=self.context['request'].user)

        return obj.total_computers()

    class Meta:
        model = Attribute
        fields = '__all__'


class AttributeInfoSerializer(serializers.ModelSerializer):
    property_att = PropertyInfoSerializer(many=False, read_only=True)

    class Meta:
        model = Attribute
        fields = ('id', 'property_att', 'value', 'description', 'latitude', 'longitude')


class AttributeSetSerializer(serializers.ModelSerializer):
    included_attributes = AttributeInfoSerializer(many=True, read_only=True)
    excluded_attributes = AttributeInfoSerializer(many=True, read_only=True)

    class Meta:
        model = AttributeSet
        fields = '__all__'


class AttributeSetWriteSerializer(AttributeRepresentationMixin, serializers.ModelSerializer):
    class Meta:
        model = AttributeSet
        fields = '__all__'


class ServerPropertyInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServerProperty
        fields = ('id', 'prefix', 'name', 'sort')


class ServerPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServerProperty
        fields = ('id', 'prefix', 'name', 'kind', 'enabled')


class ClientPropertyInfoSerializer(serializers.ModelSerializer):
    code = serializers.CharField(allow_blank=False)

    class Meta:
        model = ClientProperty
        fields = ('id', 'prefix', 'name', 'sort')


class ClientPropertySerializer(serializers.ModelSerializer):
    code = serializers.CharField(allow_blank=False)

    class Meta:
        model = ClientProperty
        fields = ('id', 'prefix', 'name', 'kind', 'sort', 'enabled', 'language', 'code')


class SingularitySerializer(serializers.ModelSerializer):
    property_att = ServerPropertyInfoSerializer(many=False, read_only=True)
    language = serializers.SerializerMethodField()
    included_attributes = AttributeInfoSerializer(many=True, read_only=True)
    excluded_attributes = AttributeInfoSerializer(many=True, read_only=True)

    @extend_schema_field(serializers.CharField)
    def get_language(self, obj):
        return obj.get_language_display()

    class Meta:
        model = Singularity
        fields = (
            'id',
            'name',
            'enabled',
            'priority',
            'property_att',
            'language',
            'code',
            'included_attributes',
            'excluded_attributes',
        )


class SingularityWriteSerializer(AttributeRepresentationMixin, serializers.ModelSerializer):
    class Meta:
        model = Singularity
        fields = '__all__'


class ServerAttributeSerializer(AttributeSerializer):
    property_att = ServerPropertyInfoSerializer(many=False, read_only=True)

    class Meta:
        model = ServerAttribute
        fields = (
            'id',
            'property_att',
            'value',
            'description',
            'latitude',
            'longitude',
            'total_computers',
        )


class ServerAttributeWriteSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        representation = super().to_representation(obj)

        representation['property_att'] = ServerPropertyInfoSerializer(obj.property_att).data

        return representation

    class Meta:
        model = ServerAttribute
        fields = ('id', 'property_att', 'value', 'description', 'latitude', 'longitude')


class ClientAttributeSerializer(AttributeSerializer):
    property_att = ServerPropertyInfoSerializer(many=False, read_only=True)

    class Meta:
        model = ClientAttribute
        fields = (
            'id',
            'property_att',
            'value',
            'description',
            'latitude',
            'longitude',
            'total_computers',
        )


class ClientAttributeWriteSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        representation = super().to_representation(obj)

        representation['property_att'] = ServerPropertyInfoSerializer(obj.property_att).data

        return representation

    class Meta:
        model = ClientAttribute
        fields = ('id', 'property_att', 'value', 'description', 'latitude', 'longitude')
