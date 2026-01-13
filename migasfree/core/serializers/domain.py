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
Domain and Scope serializers.
"""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ..models import Domain, Scope
from .base import AttributeRepresentationMixin
from .property import AttributeInfoSerializer


class DomainInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ('id', 'name')


class DomainListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ('id', 'name', 'comment')


class DomainSerializer(serializers.ModelSerializer):
    included_attributes = AttributeInfoSerializer(many=True, read_only=True)
    excluded_attributes = AttributeInfoSerializer(many=True, read_only=True)
    tags = AttributeInfoSerializer(many=True, read_only=True)
    domain_admins = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListField)
    def get_domain_admins(self, obj):
        return obj.get_domain_admins()

    class Meta:
        model = Domain
        fields = '__all__'


class DomainWriteSerializer(serializers.ModelSerializer):
    domain_admins = serializers.ListField(child=serializers.IntegerField(), allow_empty=True, write_only=True)

    def to_representation(self, obj):
        # Import here to avoid circular dependency
        from .user import UserProfileInfoSerializer

        representation = super().to_representation(obj)

        representation['included_attributes'] = [
            AttributeInfoSerializer(item).data for item in obj.included_attributes.all()
        ]

        representation['excluded_attributes'] = [
            AttributeInfoSerializer(item).data for item in obj.excluded_attributes.all()
        ]

        representation['tags'] = [AttributeInfoSerializer(item).data for item in obj.tags.all()]

        representation['domain_admins'] = [UserProfileInfoSerializer(item).data for item in obj.domains.all()]

        return representation

    def create(self, validated_data):
        users = validated_data.pop('domain_admins', None)
        instance = super().create(validated_data)
        instance.update_domain_admins(users)

        return instance

    def update(self, instance, validated_data):
        users = validated_data.pop('domain_admins', None)
        instance = super().update(instance, validated_data)
        instance.update_domain_admins(users)

        return instance

    class Meta:
        model = Domain
        fields = ('id', 'name', 'comment', 'included_attributes', 'excluded_attributes', 'tags', 'domain_admins')


class ScopeInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scope
        fields = ('id', 'name')


class ScopeListSerializer(serializers.ModelSerializer):
    # Import UserProfileInfoSerializer dynamically to avoid circular import
    def to_representation(self, instance):
        from .user import UserProfileInfoSerializer

        representation = super().to_representation(instance)
        if instance.user:
            representation['user'] = UserProfileInfoSerializer(instance.user).data
        if instance.domain:
            representation['domain'] = DomainInfoSerializer(instance.domain).data
        return representation

    class Meta:
        model = Scope
        fields = ('id', 'name', 'user', 'domain')


class ScopeSerializer(serializers.ModelSerializer):
    included_attributes = AttributeInfoSerializer(many=True, read_only=True)
    excluded_attributes = AttributeInfoSerializer(many=True, read_only=True)

    def to_representation(self, instance):
        from .user import UserProfileInfoSerializer

        representation = super().to_representation(instance)
        if instance.user:
            representation['user'] = UserProfileInfoSerializer(instance.user).data
        if instance.domain:
            representation['domain'] = DomainInfoSerializer(instance.domain).data
        return representation

    class Meta:
        model = Scope
        fields = '__all__'


class ScopeWriteSerializer(AttributeRepresentationMixin, serializers.ModelSerializer):
    def to_representation(self, obj):
        from .user import UserProfileInfoSerializer

        representation = super().to_representation(obj)

        if obj.user:
            representation['user'] = UserProfileInfoSerializer(obj.user).data

        if obj.domain:
            representation['domain'] = DomainInfoSerializer(obj.domain).data

        return representation

    class Meta:
        model = Scope
        fields = '__all__'
