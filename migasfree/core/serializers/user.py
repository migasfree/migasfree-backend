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
User, Group and Permission serializers.
"""

from dj_rest_auth.serializers import UserDetailsSerializer
from django.contrib.auth.models import Group, Permission
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ..models import UserProfile
from .domain import DomainInfoSerializer, ScopeInfoSerializer


class UserProfileInfoSerializer(UserDetailsSerializer):
    class Meta(UserDetailsSerializer.Meta):
        fields = ('id', 'username')


class PermissionInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('id', 'name', 'codename')


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'


class GroupInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name')


class GroupSerializer(serializers.ModelSerializer):
    permissions = PermissionInfoSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = '__all__'


class GroupWriteSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        representation = super().to_representation(obj)

        representation['permissions'] = [PermissionInfoSerializer(item).data for item in obj.permissions.all()]

        return representation

    class Meta:
        model = Group
        fields = '__all__'


class UserProfileWriteSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        representation = super().to_representation(obj)

        representation['groups'] = [GroupInfoSerializer(item).data for item in obj.groups.all()]

        representation['user_permissions'] = [
            PermissionInfoSerializer(item).data for item in obj.user_permissions.all()
        ]

        representation['domains'] = [DomainInfoSerializer(item).data for item in obj.domains.all()]

        if obj.domain_preference:
            representation['domain_preference'] = DomainInfoSerializer(obj.domain_preference).data

        if obj.scope_preference:
            representation['scope_preference'] = ScopeInfoSerializer(obj.scope_preference).data

        return representation

    class Meta:
        model = UserProfile
        fields = (
            *UserDetailsSerializer.Meta.fields,
            'domains',
            'domain_preference',
            'scope_preference',
            'groups',
            'user_permissions',
            'is_superuser',
            'is_staff',
            'is_active',
            'last_login',
            'date_joined',
            'id',
        )


class UserProfileListSerializer(UserDetailsSerializer):
    domain_preference = DomainInfoSerializer(many=False, read_only=True, source='userprofile.domain_preference')
    scope_preference = ScopeInfoSerializer(many=False, read_only=True, source='userprofile.scope_preference')

    class Meta(UserDetailsSerializer.Meta):
        fields = (
            *UserDetailsSerializer.Meta.fields,
            'domain_preference',
            'scope_preference',
            'is_superuser',
            'is_staff',
            'is_active',
            'last_login',
            'date_joined',
            'id',
        )


class UserProfileSerializer(UserDetailsSerializer):
    groups = GroupInfoSerializer(many=True, read_only=True)
    user_permissions = PermissionInfoSerializer(many=True, read_only=True)
    domains = DomainInfoSerializer(many=True, read_only=True, source='userprofile.domains')
    domain_preference = DomainInfoSerializer(many=False, read_only=True, source='userprofile.domain_preference')
    scope_preference = ScopeInfoSerializer(many=False, read_only=True, source='userprofile.scope_preference')
    token = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField)
    def get_token(self, obj):
        try:
            return obj.get_token()
        except AttributeError:
            return ''  # rest-auth/user/

    class Meta(UserDetailsSerializer.Meta):
        fields = (
            *UserDetailsSerializer.Meta.fields,
            'domains',
            'domain_preference',
            'scope_preference',
            'groups',
            'user_permissions',
            'is_superuser',
            'is_staff',
            'is_active',
            'last_login',
            'date_joined',
            'id',
            'token',
        )


class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if len(attrs['password']) < 8:
            raise serializers.ValidationError({'password': _('Minimum length is %d characters') % 8})

        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': _("Password fields didn't match.")})

        return attrs
