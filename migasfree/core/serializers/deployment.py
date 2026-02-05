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
Deployment serializers.
"""

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ...client.models import Computer
from ...utils import cmp, to_list
from ..models import Deployment, Domain, ExternalSource, InternalSource
from ..pms import tasks
from .package import PackageInfoSerializer, PackageSetInfoSerializer
from .platform import ProjectInfoSerializer
from .property import AttributeInfoSerializer
from .schedule import ScheduleInfoSerializer


class DomainInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ('id', 'name')


class DeploymentListSerializer(serializers.ModelSerializer):
    project = ProjectInfoSerializer(many=False, read_only=True)
    domain = DomainInfoSerializer(many=False, read_only=True)
    schedule = ScheduleInfoSerializer(many=False, read_only=True)
    schedule_timeline = serializers.SerializerMethodField()

    def get_schedule_timeline(self, obj):
        return obj.schedule_timeline()

    class Meta:
        model = Deployment
        fields = (
            'id',
            'project',
            'domain',
            'schedule',
            'source',
            'frozen',
            'name',
            'slug',
            'comment',
            'start_date',
            'enabled',
            'auto_restart',
            'schedule_timeline',
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
            'id',
            'enabled',
            'project',
            'domain',
            'name',
            'slug',
            'comment',
            'available_packages',
            'included_attributes',
            'excluded_attributes',
            'packages_to_install',
            'packages_to_remove',
            'default_preincluded_packages',
            'default_included_packages',
            'default_excluded_packages',
            'schedule',
            'start_date',
            'auto_restart',
        )


class ExternalSourceSerializer(DeploymentSerializer):
    class Meta:
        model = ExternalSource
        fields = (
            'id',
            'enabled',
            'project',
            'domain',
            'name',
            'slug',
            'comment',
            'included_attributes',
            'excluded_attributes',
            'packages_to_install',
            'packages_to_remove',
            'default_preincluded_packages',
            'default_included_packages',
            'default_excluded_packages',
            'schedule',
            'start_date',
            'auto_restart',
            'base_url',
            'options',
            'suite',
            'components',
            'frozen',
            'expire',
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
                        _('It is not possible to assign an inactive computer (%s) as an attribute') % computer.__str__()
                    )

    def validate(self, data):
        for item in data.get('available_packages', []):
            if item.project.id != data['project'].id:
                raise serializers.ValidationError(
                    _('Package %(pkg)s must belong to the project %(project)s')
                    % {'pkg': item, 'project': data['project']}
                )

        self._validate_active_computers(data.get('included_attributes', []))
        self._validate_active_computers(data.get('excluded_attributes', []))

        return data

    def create(self, validated_data):
        deploy = super().create(validated_data)
        if deploy.source == Deployment.SOURCE_INTERNAL:
            tasks.create_repository_metadata.apply_async(
                queue=f'pms-{deploy.pms().name}', kwargs={'payload': deploy.get_repository_metadata_payload()}
            )

        return deploy

    def update(self, instance, validated_data):
        if instance.source == Deployment.SOURCE_INTERNAL and 'name' in validated_data:
            old_obj = self.Meta.model.objects.get(id=instance.id)
            old_pkgs = sorted(old_obj.available_packages.values_list('id', flat=True))
            old_name = old_obj.name

        # https://github.com/tomchristie/django-rest-framework/issues/2442
        instance = super().update(instance, validated_data)
        if instance.source == Deployment.SOURCE_INTERNAL and 'name' in validated_data:
            new_pkgs = sorted(instance.available_packages.values_list('id', flat=True))

            if cmp(old_pkgs, new_pkgs) != 0 or old_name != validated_data['name']:
                tasks.create_repository_metadata.apply_async(
                    queue=f'pms-{instance.pms().name}',
                    kwargs={'payload': instance.get_repository_metadata_payload()},
                )

                if old_name != validated_data['name']:
                    removal_payload = {
                        'project': {
                            'slug': old_obj.project.slug,
                            'pms': old_obj.project.pms,
                        },
                        'slug': old_obj.slug,
                    }
                    tasks.remove_repository_metadata.delay(removal_payload)

        return instance

    class Meta:
        model = Deployment
        fields = '__all__'


class InternalSourceWriteSerializer(DeploymentWriteSerializer):
    class Meta:
        model = InternalSource
        fields = (
            'id',
            'enabled',
            'project',
            'domain',
            'name',
            'comment',
            'available_packages',
            'available_package_sets',
            'included_attributes',
            'excluded_attributes',
            'packages_to_install',
            'packages_to_remove',
            'default_preincluded_packages',
            'default_included_packages',
            'default_excluded_packages',
            'schedule',
            'start_date',
            'auto_restart',
        )


class ExternalSourceWriteSerializer(DeploymentWriteSerializer):
    class Meta:
        model = ExternalSource
        fields = (
            'id',
            'enabled',
            'project',
            'domain',
            'name',
            'comment',
            'included_attributes',
            'excluded_attributes',
            'packages_to_install',
            'packages_to_remove',
            'default_preincluded_packages',
            'default_included_packages',
            'default_excluded_packages',
            'schedule',
            'start_date',
            'auto_restart',
            'base_url',
            'options',
            'suite',
            'components',
            'frozen',
            'expire',
        )
