# -*- coding: utf-8 -*-

# Copyright (c) 2015-2020 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2020 Alberto Gacías <alberto@migasfree.org>
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

from past.builtins import cmp

from django.contrib.auth.models import Group, Permission
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_auth.serializers import UserDetailsSerializer

from migasfree.client.models import Computer

from . import tasks

from .validators import (
    MimetypeValidator, validate_package_name, validate_project_pms
)
from .pms import get_available_mimetypes
from .models import (
    Platform, Project, Store,
    ServerProperty, ClientProperty, Property,
    Attribute, ServerAttribute, ClientAttribute,
    Schedule, ScheduleDelay,
    Package, Deployment, AttributeSet,
    Domain, Scope, UserProfile,
    InternalSource, ExternalSource,
)
from ..utils import to_list


class PropertyInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ('id', 'prefix')


class PropertyWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = '__all__'


class PropertySerializer(serializers.ModelSerializer):
    language = serializers.SerializerMethodField()

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
        fields = ('id', 'property_att', 'value')


class AttributeSetSerializer(serializers.ModelSerializer):
    included_attributes = AttributeInfoSerializer(many=True, read_only=True)
    excluded_attributes = AttributeInfoSerializer(many=True, read_only=True)

    class Meta:
        model = AttributeSet
        fields = '__all__'


class AttributeSetWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeSet
        fields = '__all__'


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platform
        fields = '__all__'


class ProjectInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'name')


class ProjectSerializer(serializers.ModelSerializer):
    platform = PlatformSerializer(many=False, read_only=True)

    class Meta:
        model = Project
        fields = (
            'id', 'name', 'pms',
            'architecture', 'auto_register_computers', 'platform'
        )


class ProjectWriteSerializer(serializers.ModelSerializer):
    def init(self, *args, **kwargs):
        super(ProjectWriteSerializer, self).__init__(*args, **kwargs)
        self.fields['pms'].validators.append(validate_project_pms)

    class Meta:
        model = Project
        fields = (
            'id', 'name', 'pms',
            'architecture', 'auto_register_computers', 'platform'
        )


class StoreInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('id', 'name')


class StoreSerializer(serializers.ModelSerializer):
    project = ProjectInfoSerializer(many=False, read_only=True)

    class Meta:
        model = Store
        fields = ('id', 'name', 'project')


class StoreWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('id', 'name', 'project')


class ServerPropertyInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServerProperty
        fields = ('id', 'prefix', 'name')


class ServerPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServerProperty
        fields = ('id', 'prefix', 'name', 'kind', 'enabled')


class ClientPropertyInfoSerializer(serializers.ModelSerializer):
    code = serializers.CharField(allow_blank=False)

    class Meta:
        model = ClientProperty
        fields = ('id', 'prefix', 'name')


class ClientPropertySerializer(serializers.ModelSerializer):
    code = serializers.CharField(allow_blank=False)

    class Meta:
        model = ClientProperty
        fields = ('id', 'prefix', 'name', 'kind', 'enabled', 'language', 'code')


class ServerAttributeSerializer(serializers.ModelSerializer):
    property_att = ServerPropertyInfoSerializer(many=False, read_only=True)

    class Meta:
        model = ServerAttribute
        fields = ('id', 'property_att', 'value', 'description')


class ServerAttributeWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServerAttribute
        fields = ('id', 'property_att', 'value', 'description')


class ClientAttributeSerializer(serializers.ModelSerializer):
    property_att = ServerPropertyInfoSerializer(many=False, read_only=True)

    class Meta:
        model = ClientAttribute
        fields = ('id', 'property_att', 'value', 'description')


class ClientAttributeWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientAttribute
        fields = ('id', 'property_att', 'value', 'description')


class ScheduleDelaySerializer(serializers.ModelSerializer):
    attributes = AttributeSerializer(many=True)

    class Meta:
        model = ScheduleDelay
        fields = '__all__'


class ScheduleDelayWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleDelay
        fields = '__all__'


class ScheduleInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ('id', 'name')


class ScheduleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = '__all__'


class ScheduleSerializer(serializers.ModelSerializer):
    delays = ScheduleDelaySerializer(many=True)

    class Meta:
        model = Schedule
        fields = ('id', 'name', 'description', 'number_delays', 'delays')


class PackageInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ('id', 'name')


class PackageSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all()
    )
    store = serializers.PrimaryKeyRelatedField(
        queryset=Store.objects.all()
    )
    files = serializers.FileField(
        allow_empty_file=False,
        validators=[MimetypeValidator(get_available_mimetypes())]
    )
    name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True
    )

    def to_representation(self, obj):
        return {
            'id': obj.id,
            'name': obj.name,
            'version': obj.version,
            'architecture': obj.architecture,
            'project': {
                'id': obj.project.id,
                'name': obj.project.name,
            },
            'store': {
                'id': obj.store.id if obj.store else 0,
                'name': obj.store.name if obj.store else ''
            }
        }

    def create(self, validated_data):
        file_list = validated_data['files']
        if not isinstance(file_list, list):
            file_list = [file_list]  # always multiple files

        validate_package_name(validated_data['name'], file_list)
        if validated_data['name'] == '' and len(file_list) == 1:
            validated_data['name'] = file_list[0].name
        else:
            validated_data['name'] = slugify(validated_data['name'])

        return Package.objects.create(
            name=validated_data['name'],
            project=validated_data['project'],
            store=validated_data['store'],
            file_list=file_list
        )

    class Meta:
        model = Package
        fields = ('id', 'name', 'project', 'store', 'files')


class DeploymentSerializer(serializers.ModelSerializer):
    project = ProjectInfoSerializer(many=False, read_only=True)
    schedule = ScheduleInfoSerializer(many=False, read_only=True)
    included_attributes = AttributeInfoSerializer(many=True, read_only=True)
    excluded_attributes = AttributeInfoSerializer(many=True, read_only=True)

    packages_to_install = serializers.SerializerMethodField()
    packages_to_remove = serializers.SerializerMethodField()
    default_preincluded_packages = serializers.SerializerMethodField()
    default_included_packages = serializers.SerializerMethodField()
    default_excluded_packages = serializers.SerializerMethodField()

    def get_packages_to_install(self, obj):
        return to_list(obj.packages_to_install)

    def get_packages_to_remove(self, obj):
        return to_list(obj.packages_to_remove)

    def get_default_preincluded_packages(self, obj):
        return to_list(obj.default_preincluded_packages)

    def get_default_included_packages(self, obj):
        return to_list(obj.default_included_packages)

    def get_default_excluded_packages(self, obj):
        return to_list(obj.default_excluded_packages)

    class Meta:
        model = Deployment
        fields = '__all__'


class InternalSourceSerializer(DeploymentSerializer):
    available_packages = PackageInfoSerializer(many=True, read_only=True)

    class Meta:
        model = InternalSource
        fields = (
            'id', 'enabled', 'project', 'domain', 'name', 'slug', 'comment',
            'available_packages',
            'included_attributes', 'excluded_attributes',
            'packages_to_install', 'packages_to_remove',
            'default_preincluded_packages', 'default_included_packages', 'default_excluded_packages',
            'schedule', 'start_date'
        )


class ExternalSourceSerializer(DeploymentSerializer):
    class Meta:
        model = ExternalSource
        fields = (
            'id', 'enabled', 'project', 'domain', 'name', 'slug', 'comment',
            'included_attributes', 'excluded_attributes',
            'packages_to_install', 'packages_to_remove',
            'default_preincluded_packages', 'default_included_packages', 'default_excluded_packages',
            'schedule', 'start_date',
            'base_url', 'options', 'suite', 'components', 'frozen', 'expire'
        )


class DeploymentWriteSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(read_only=True)

    def to_internal_value(self, data):
        """
        :param data: {
            "enabled": true,
            "project": id,
            "domain": id,
            "name": "string",
            "comment": "string",
            "available_packages": ["string", ...],
            "start_date": "string",
            "packages_to_install": [],
            "packages_to_remove": [],
            "default_preincluded_packages": [],
            "default_included_packages": [],
            "default_excluded_packages": [],
            "schedule": id,
            "included_attributes": [id1, id2, ...],
            "excluded_attributes": [id1, ...]
        }
        :return: Deployment object
        """
        if 'packages_to_install' in data:
            data['packages_to_install'] = '\n'.join(data.get('packages_to_install', []))

        if 'packages_to_remove' in data:
            data['packages_to_remove'] = '\n'.join(data.get('packages_to_remove', []))

        if 'default_preincluded_packages' in data:
            data['default_preincluded_packages'] = '\n'.join(data.get('default_preincluded_packages', []))

        if 'default_included_packages' in data:
            data['default_included_packages'] = '\n'.join(data.get('default_included_packages', []))

        if 'default_excluded_packages' in data:
            data['default_excluded_packages'] = '\n'.join(data.get('default_excluded_packages', []))

        return super(DeploymentWriteSerializer, self).to_internal_value(data)

    def _validate_active_computers(self, att_list):
        for attribute in att_list:
            if attribute.property_att.prefix == 'CID':
                computer = Computer.objects.get(pk=int(attribute.value))
                if computer.status not in Computer.ACTIVE_STATUS:
                    raise serializers.ValidationError(
                        _('It is not possible to assign an inactive computer (%s) as an attribute')
                        % computer.__str__()
                    )

    def validate(self, data):
        for item in data.get('available_packages', []):
            if item.project.id != data['project'].id:
                raise serializers.ValidationError(
                    _('Package %s must belong to the project %s') % (
                        item, data['project']
                    )
                )

        self._validate_active_computers(data.get('included_attributes', []))
        self._validate_active_computers(data.get('excluded_attributes', []))

        return data

    class Meta:
        model = Deployment
        fields = '__all__'


class InternalSourceWriteSerializer(DeploymentWriteSerializer):
    def create(self, validated_data):
        deploy = super(InternalSourceWriteSerializer, self).create(validated_data)
        tasks.create_repository_metadata.delay(deploy.id)
        return deploy

    def update(self, instance, validated_data):
        old_obj = self.Meta.model.objects.get(id=instance.id)
        old_pkgs = sorted(
            old_obj.available_packages.values_list('id', flat=True)
        )
        old_name = old_obj.name

        # https://github.com/tomchristie/django-rest-framework/issues/2442
        instance = super(InternalSourceWriteSerializer, self).update(
            instance, validated_data
        )
        new_pkgs = sorted(
            instance.available_packages.values_list('id', flat=True)
        )

        if cmp(old_pkgs, new_pkgs) != 0 or old_name != validated_data['name']:
            tasks.create_repository_metadata.delay(instance.id)

            if old_name != validated_data['name']:
                tasks.remove_repository_metadata.delay(
                    instance.id, old_obj.slug
                )

        return instance

    class Meta:
        model = InternalSource
        fields = (
            'id', 'enabled', 'project', 'domain', 'name', 'comment',
            'available_packages', 'available_package_sets',
            'included_attributes', 'excluded_attributes',
            'packages_to_install', 'packages_to_remove',
            'default_preincluded_packages', 'default_included_packages', 'default_excluded_packages',
            'schedule', 'start_date'
        )


class ExternalSourceWriteSerializer(DeploymentWriteSerializer):
    class Meta:
        model = ExternalSource
        fields = (
            'id', 'enabled', 'project', 'domain', 'name', 'comment',
            'included_attributes', 'excluded_attributes',
            'packages_to_install', 'packages_to_remove',
            'default_preincluded_packages', 'default_included_packages', 'default_excluded_packages',
            'schedule', 'start_date',
            'base_url', 'options', 'suite', 'components', 'frozen', 'expire'
        )


class DomainInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ('id', 'name')


class DomainSerializer(serializers.ModelSerializer):
    included_attributes = AttributeInfoSerializer(many=True, read_only=True)
    excluded_attributes = AttributeInfoSerializer(many=True, read_only=True)
    tags = AttributeInfoSerializer(many=True, read_only=True)

    class Meta:
        model = Domain
        fields = '__all__'


class DomainWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = '__all__'


class UserProfileInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('id', 'username')


class ScopeInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scope
        fields = ('id', 'name')


class ScopeSerializer(serializers.ModelSerializer):
    included_attributes = AttributeInfoSerializer(many=True, read_only=True)
    excluded_attributes = AttributeInfoSerializer(many=True, read_only=True)
    user = UserProfileInfoSerializer(many=False, read_only=True)
    domain = DomainInfoSerializer(many=False, read_only=True)

    class Meta:
        model = Scope
        fields = '__all__'


class ScopeWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scope
        fields = '__all__'


class PermissionInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('id', 'name')


class GroupInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name')


class UserProfileSerializer(UserDetailsSerializer):
    groups = GroupInfoSerializer(many=True, read_only=True)
    user_permissions = PermissionInfoSerializer(many=True, read_only=True)
    domains = DomainInfoSerializer(many=True, read_only=True, source='userprofile.domains')
    domain_preference = serializers.IntegerField(source='userprofile.domain_preference.id', allow_null=True)
    scope_preference = serializers.IntegerField(source='userprofile.scope_preference.id', allow_null=True)

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('userprofile', {})
        domain_preference = profile_data.get('domain_preference')
        scope_preference = profile_data.get('scope_preference')

        instance = super(UserProfileSerializer, self).update(instance, validated_data)

        # get and update user profile
        profile = instance.userprofile
        if domain_preference:
            pk = domain_preference.get('id', 0)
            if pk:
                domain = get_object_or_404(Domain, pk=pk)
                if domain.id in list(profile.domains.values_list('id', flat=True)):
                    profile.update_domain(domain)
            else:
                profile.update_domain(0)
        if scope_preference:
            pk = scope_preference.get('id', 0)
            if pk:
                scope = get_object_or_404(Scope, pk=pk)
                profile.update_scope(scope)
            else:
                profile.update_scope(0)

        return instance

    class Meta(UserDetailsSerializer.Meta):
        fields = UserDetailsSerializer.Meta.fields + (
            'domains', 'domain_preference', 'scope_preference',
            'groups', 'user_permissions',
        )
