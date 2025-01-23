# -*- coding: utf-8 -*-

# Copyright (c) 2015-2025 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2025 Alberto Gacías <alberto@migasfree.org>
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

from django.contrib.auth.models import Group, Permission
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from dj_rest_auth.serializers import UserDetailsSerializer

from ..client.models import Computer
from ..utils import cmp

from .pms import tasks

from .validators import MimetypeValidator, validate_project_pms
from .pms import get_available_mimetypes
from .models import (
    Platform, Project, Store,
    ServerProperty, ClientProperty,
    Property, Singularity,
    Attribute, AttributeSet,
    ServerAttribute, ClientAttribute,
    Schedule, ScheduleDelay,
    Package, PackageSet, Deployment,
    Domain, Scope, UserProfile,
    InternalSource, ExternalSource,
)
from ..utils import to_list


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
        fields = (
            'id', 'property_att',
            'value', 'description',
            'latitude', 'longitude'
        )


class AttributeSetSerializer(serializers.ModelSerializer):
    included_attributes = AttributeInfoSerializer(many=True, read_only=True)
    excluded_attributes = AttributeInfoSerializer(many=True, read_only=True)

    class Meta:
        model = AttributeSet
        fields = '__all__'


class AttributeSetWriteSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        representation = super().to_representation(obj)

        representation['included_attributes'] = [
            AttributeInfoSerializer(item).data for item in obj.included_attributes.all()
        ]

        representation['excluded_attributes'] = [
            AttributeInfoSerializer(item).data for item in obj.excluded_attributes.all()
        ]

        return representation

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
        fields = (
            'id', 'name', 'slug', 'pms',
            'architecture', 'auto_register_computers',
            'base_os', 'platform'
        )


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
        fields = (
            'id', 'name', 'pms',
            'architecture', 'auto_register_computers',
            'base_os', 'platform'
        )


class StoreInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('id', 'name', 'slug')


class StoreSerializer(serializers.ModelSerializer):
    project = ProjectInfoSerializer(many=False, read_only=True)

    class Meta:
        model = Store
        fields = ('id', 'name', 'slug', 'project')


class StoreWriteSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        representation = super().to_representation(obj)

        if obj.project:
            representation['project'] = ProjectInfoSerializer(obj.project).data

        return representation

    class Meta:
        model = Store
        fields = ('id', 'name', 'project')


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
        fields = (
            'id', 'prefix', 'name',
            'kind', 'sort', 'enabled',
            'language', 'code'
        )


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
            'id', 'name', 'enabled', 'priority',
            'property_att', 'language', 'code',
            'included_attributes', 'excluded_attributes',
        )


class SingularityWriteSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        representation = super().to_representation(obj)

        representation['included_attributes'] = [
            AttributeInfoSerializer(item).data for item in obj.included_attributes.all()
        ]

        representation['excluded_attributes'] = [
            AttributeInfoSerializer(item).data for item in obj.excluded_attributes.all()
        ]

        return representation

    class Meta:
        model = Singularity
        fields = '__all__'


class ServerAttributeSerializer(AttributeSerializer):
    property_att = ServerPropertyInfoSerializer(many=False, read_only=True)

    class Meta:
        model = ServerAttribute
        fields = (
            'id', 'property_att',
            'value', 'description',
            'latitude', 'longitude',
            'total_computers',
        )


class ServerAttributeWriteSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        representation = super().to_representation(obj)

        representation['property_att'] = ServerPropertyInfoSerializer(obj.property_att).data

        return representation

    class Meta:
        model = ServerAttribute
        fields = (
            'id', 'property_att',
            'value', 'description',
            'latitude', 'longitude'
        )


class ClientAttributeSerializer(AttributeSerializer):
    property_att = ServerPropertyInfoSerializer(many=False, read_only=True)

    class Meta:
        model = ClientAttribute
        fields = (
            'id', 'property_att',
            'value', 'description',
            'latitude', 'longitude',
            'total_computers',
        )


class ClientAttributeWriteSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        representation = super().to_representation(obj)

        representation['property_att'] = ServerPropertyInfoSerializer(obj.property_att).data

        return representation

    class Meta:
        model = ClientAttribute
        fields = (
            'id', 'property_att',
            'value', 'description',
            'latitude', 'longitude'
        )


class ScheduleInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ('id', 'name')


class ScheduleDelaySerializer(serializers.ModelSerializer):
    attributes = AttributeSerializer(many=True)
    schedule = ScheduleInfoSerializer(many=False, read_only=True)

    class Meta:
        model = ScheduleDelay
        fields = ('id', 'delay', 'duration', 'attributes', 'schedule')


class ScheduleDelayWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleDelay
        fields = '__all__'


class ScheduleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = '__all__'


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ('id', 'name', 'description', 'delays_count')


class PackageInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ('id', 'fullname')


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
    fullname = serializers.CharField(
        max_length=170,
        required=False,
        allow_blank=True
    )

    def to_representation(self, obj):
        return {
            'id': obj.id,
            'fullname': obj.fullname,
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
            },
            'url': obj.url()
        }

    def create(self, validated_data):
        file_ = validated_data['files']

        # validate_package_name(validated_data['name'], file_)
        if validated_data['fullname'] == '' and file_:
            validated_data['fullname'] = file_.name
        else:
            validated_data['fullname'] = slugify(validated_data['fullname'])

        if validated_data['name'] == '':
            validated_data['name'], validated_data['version'], validated_data['architecture'] = Package.normalized_name(
                validated_data['fullname']
            )

        return Package.objects.create(
            fullname=validated_data['fullname'],
            name=validated_data['name'],
            version=validated_data['version'],
            architecture=validated_data['architecture'],
            project=validated_data['project'],
            store=validated_data['store'],
            file_=file_
        )

    class Meta:
        model = Package
        fields = ('id', 'fullname', 'name', 'project', 'store', 'files')


class PackageSetInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageSet
        fields = ('id', 'name')


class PackageSetSerializer(serializers.ModelSerializer):
    project = ProjectInfoSerializer(many=False, read_only=True)
    store = StoreInfoSerializer(many=False, read_only=True)
    packages = PackageInfoSerializer(many=True, read_only=True)

    class Meta:
        model = PackageSet
        fields = '__all__'


class PackageSetWriteSerializer(serializers.ModelSerializer):
    """
    files = serializers.ListField(
        child=serializers.FileField(
            allow_empty_file=True,
            validators=[MimetypeValidator(get_available_mimetypes())]
        ),
        required=False,
    )
    files = serializers.FileField(
        allow_empty_file=True,
        validators=[MimetypeValidator(get_available_mimetypes())],
        required=False,
    )
    """

    class Meta:
        model = PackageSet
        fields = '__all__'


class DomainInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ('id', 'name')


class DeploymentListSerializer(serializers.ModelSerializer):
    project = ProjectInfoSerializer(many=False, read_only=True)
    domain = DomainInfoSerializer(many=False, read_only=True)
    schedule = ScheduleInfoSerializer(many=False, read_only=True)

    class Meta:
        model = Deployment
        fields = (
            'id', 'project', 'domain',
            'schedule', 'source',
            'name', 'slug', 'comment',
            'start_date', 'enabled', 'auto_restart',
        )


class DeploymentSerializer(serializers.ModelSerializer):
    project = ProjectInfoSerializer(many=False, read_only=True)
    domain = DomainInfoSerializer(many=False, read_only=True)
    schedule = ScheduleInfoSerializer(many=False, read_only=True)
    included_attributes = AttributeInfoSerializer(many=True, read_only=True)
    excluded_attributes = AttributeInfoSerializer(many=True, read_only=True)

    packages_to_install = serializers.SerializerMethodField()
    packages_to_remove = serializers.SerializerMethodField()
    default_preincluded_packages = serializers.SerializerMethodField()
    default_included_packages = serializers.SerializerMethodField()
    default_excluded_packages = serializers.SerializerMethodField()

    available_packages = PackageInfoSerializer(many=True, read_only=True)
    available_package_sets = PackageSetInfoSerializer(many=True, read_only=True)

    @extend_schema_field(serializers.ListField)
    def get_packages_to_install(self, obj):
        return to_list(obj.packages_to_install)

    @extend_schema_field(serializers.ListField)
    def get_packages_to_remove(self, obj):
        return to_list(obj.packages_to_remove)

    @extend_schema_field(serializers.ListField)
    def get_default_preincluded_packages(self, obj):
        return to_list(obj.default_preincluded_packages)

    @extend_schema_field(serializers.ListField)
    def get_default_included_packages(self, obj):
        return to_list(obj.default_included_packages)

    @extend_schema_field(serializers.ListField)
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
            'schedule', 'start_date', 'auto_restart',
        )


class ExternalSourceSerializer(DeploymentSerializer):
    class Meta:
        model = ExternalSource
        fields = (
            'id', 'enabled', 'project', 'domain', 'name', 'slug', 'comment',
            'included_attributes', 'excluded_attributes',
            'packages_to_install', 'packages_to_remove',
            'default_preincluded_packages', 'default_included_packages', 'default_excluded_packages',
            'schedule', 'start_date', 'auto_restart',
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
            "available_packages": [id1, id2, ...],
            "available_package_sets": [id1, id2, ...],
            "start_date": "string",
            "auto_restart": false,
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

        return super().to_internal_value(data)

    def to_representation(self, obj):
        representation = super().to_representation(obj)

        representation['project'] = ProjectInfoSerializer(obj.project).data

        representation['included_attributes'] = [
            AttributeInfoSerializer(item).data for item in obj.included_attributes.all()
        ]

        representation['excluded_attributes'] = [
            AttributeInfoSerializer(item).data for item in obj.excluded_attributes.all()
        ]

        representation['available_packages'] = [
            PackageInfoSerializer(item).data for item in obj.available_packages.all()
        ]

        representation['available_package_sets'] = [
            PackageSetInfoSerializer(item).data for item in obj.available_package_sets.all()
        ]

        representation['packages_to_install'] = to_list(obj.packages_to_install)
        representation['packages_to_remove'] = to_list(obj.packages_to_remove)
        representation['default_preincluded_packages'] = to_list(obj.default_preincluded_packages)
        representation['default_included_packages'] = to_list(obj.default_included_packages)
        representation['default_excluded_packages'] = to_list(obj.default_excluded_packages)

        return representation

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
                    _('Package %(pkg)s must belong to the project %(project)s') % {
                        'pkg': item, 'project': data['project']
                    }
                )

        self._validate_active_computers(data.get('included_attributes', []))
        self._validate_active_computers(data.get('excluded_attributes', []))

        return data

    def create(self, validated_data):
        deploy = super().create(validated_data)
        if deploy.source == Deployment.SOURCE_INTERNAL:
            tasks.create_repository_metadata.apply_async(
                queue=f'pms-{deploy.pms().name}',
                kwargs={'deployment_id': deploy.id}
            )

        return deploy

    def update(self, instance, validated_data):
        if instance.source == Deployment.SOURCE_INTERNAL and 'name' in validated_data:
            old_obj = self.Meta.model.objects.get(id=instance.id)
            old_pkgs = sorted(
                old_obj.available_packages.values_list('id', flat=True)
            )
            old_name = old_obj.name

        # https://github.com/tomchristie/django-rest-framework/issues/2442
        instance = super().update(instance, validated_data)
        if instance.source == Deployment.SOURCE_INTERNAL and 'name' in validated_data:
            new_pkgs = sorted(
                instance.available_packages.values_list('id', flat=True)
            )

            if cmp(old_pkgs, new_pkgs) != 0 or old_name != validated_data['name']:
                tasks.create_repository_metadata.apply_async(
                    queue=f'pms-{instance.pms().name}',
                    kwargs={'deployment_id': instance.id}
                )

                if old_name != validated_data['name']:
                    tasks.remove_repository_metadata.delay(
                        instance.id, old_obj.slug
                    )

        return instance

    class Meta:
        model = Deployment
        fields = '__all__'


class InternalSourceWriteSerializer(DeploymentWriteSerializer):
    class Meta:
        model = InternalSource
        fields = (
            'id', 'enabled', 'project', 'domain', 'name', 'comment',
            'available_packages', 'available_package_sets',
            'included_attributes', 'excluded_attributes',
            'packages_to_install', 'packages_to_remove',
            'default_preincluded_packages', 'default_included_packages', 'default_excluded_packages',
            'schedule', 'start_date', 'auto_restart',
        )


class ExternalSourceWriteSerializer(DeploymentWriteSerializer):
    class Meta:
        model = ExternalSource
        fields = (
            'id', 'enabled', 'project', 'domain', 'name', 'comment',
            'included_attributes', 'excluded_attributes',
            'packages_to_install', 'packages_to_remove',
            'default_preincluded_packages', 'default_included_packages', 'default_excluded_packages',
            'schedule', 'start_date', 'auto_restart',
            'base_url', 'options', 'suite', 'components', 'frozen', 'expire'
        )


class UserProfileInfoSerializer(UserDetailsSerializer):
    class Meta(UserDetailsSerializer.Meta):
        fields = ('id', 'username')


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
    domain_admins = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True,
        write_only=True
    )

    def to_representation(self, obj):
        representation = super().to_representation(obj)

        representation['included_attributes'] = [
            AttributeInfoSerializer(item).data for item in obj.included_attributes.all()
        ]

        representation['excluded_attributes'] = [
            AttributeInfoSerializer(item).data for item in obj.excluded_attributes.all()
        ]

        representation['tags'] = [
            AttributeInfoSerializer(item).data for item in obj.tags.all()
        ]

        representation['domain_admins'] = [
            UserProfileInfoSerializer(item).data for item in obj.domains.all()
        ]

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
        fields = (
            'id', 'name', 'comment',
            'included_attributes', 'excluded_attributes',
            'tags', 'domain_admins'
        )


class ScopeInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scope
        fields = ('id', 'name')


class ScopeListSerializer(serializers.ModelSerializer):
    user = UserProfileInfoSerializer(many=False, read_only=True)
    domain = DomainInfoSerializer(many=False, read_only=True)

    class Meta:
        model = Scope
        fields = ('id', 'name', 'user', 'domain')


class ScopeSerializer(serializers.ModelSerializer):
    included_attributes = AttributeInfoSerializer(many=True, read_only=True)
    excluded_attributes = AttributeInfoSerializer(many=True, read_only=True)
    user = UserProfileInfoSerializer(many=False, read_only=True)
    domain = DomainInfoSerializer(many=False, read_only=True)

    class Meta:
        model = Scope
        fields = '__all__'


class ScopeWriteSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        representation = super().to_representation(obj)

        representation['included_attributes'] = [
            AttributeInfoSerializer(item).data for item in obj.included_attributes.all()
        ]

        representation['excluded_attributes'] = [
            AttributeInfoSerializer(item).data for item in obj.excluded_attributes.all()
        ]

        if obj.user:
            representation['user'] = UserProfileInfoSerializer(obj.user).data

        if obj.domain:
            representation['domain'] = DomainInfoSerializer(obj.domain).data

        return representation

    class Meta:
        model = Scope
        fields = '__all__'


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

        representation['permissions'] = [
            PermissionInfoSerializer(item).data for item in obj.permissions.all()
        ]

        return representation

    class Meta:
        model = Group
        fields = '__all__'


class UserProfileWriteSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        representation = super().to_representation(obj)

        representation['groups'] = [
            GroupInfoSerializer(item).data for item in obj.groups.all()
        ]

        representation['user_permissions'] = [
            PermissionInfoSerializer(item).data for item in obj.user_permissions.all()
        ]

        representation['domains'] = [
            DomainInfoSerializer(item).data for item in obj.domains.all()
        ]

        if obj.domain_preference:
            representation['domain_preference'] = DomainInfoSerializer(
                obj.domain_preference
            ).data

        if obj.scope_preference:
            representation['scope_preference'] = ScopeInfoSerializer(
                obj.scope_preference
            ).data

        return representation

    class Meta:
        model = UserProfile
        fields = UserDetailsSerializer.Meta.fields + (
            'domains', 'domain_preference', 'scope_preference',
            'groups', 'user_permissions', 'is_superuser', 'is_staff',
            'is_active', 'last_login', 'date_joined', 'id',
        )


class UserProfileListSerializer(UserDetailsSerializer):
    domain_preference = DomainInfoSerializer(
        many=False, read_only=True, source='userprofile.domain_preference'
    )
    scope_preference = ScopeInfoSerializer(
        many=False, read_only=True, source='userprofile.scope_preference'
    )

    class Meta(UserDetailsSerializer.Meta):
        fields = UserDetailsSerializer.Meta.fields + (
            'domain_preference', 'scope_preference',
            'is_superuser', 'is_staff',
            'is_active', 'last_login', 'date_joined', 'id',
        )


class UserProfileSerializer(UserDetailsSerializer):
    groups = GroupInfoSerializer(many=True, read_only=True)
    user_permissions = PermissionInfoSerializer(many=True, read_only=True)
    domains = DomainInfoSerializer(
        many=True, read_only=True, source='userprofile.domains'
    )
    domain_preference = DomainInfoSerializer(
        many=False, read_only=True, source='userprofile.domain_preference'
    )
    scope_preference = ScopeInfoSerializer(
        many=False, read_only=True, source='userprofile.scope_preference'
    )
    token = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField)
    def get_token(self, obj):
        try:
            return obj.get_token()
        except AttributeError:
            return ''  # rest-auth/user/

    class Meta(UserDetailsSerializer.Meta):
        fields = UserDetailsSerializer.Meta.fields + (
            'domains', 'domain_preference', 'scope_preference',
            'groups', 'user_permissions', 'is_superuser', 'is_staff',
            'is_active', 'last_login', 'date_joined', 'id', 'token',
        )


class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if len(attrs['password']) < 8:
            raise serializers.ValidationError(
                {'password': _('Minimum length is %d characters') % 8}
            )

        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {'password': _("Password fields didn't match.")}
            )

        return attrs
