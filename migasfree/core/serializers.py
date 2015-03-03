# -*- coding: utf-8 -*-

# Copyright (c) 2015 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015 Alberto Gacías <alberto@migasfree.org>
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

from django.contrib.auth.models import User, Group
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from .validators import (
    MimetypeValidator, validate_package_name, validate_project_pms
)
from .pms import get_available_mimetypes
from .models import (
    Platform, Project, Store,
    ServerProperty, ClientProperty,
    Attribute, ServerAttribute, ClientAttribute,
    Schedule, ScheduleDelay,
    Package, Repository,
)


'''
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'id', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'id', 'name')
'''


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platform
        fields = ('id', 'name')


class ProjectSerializer(serializers.ModelSerializer):
    def init(self, *args, **kwargs):
        super(ProjectSerializer, self).__init__(*args, **kwargs)
        self.fields['pms'].validators.append(validate_project_pms)

    class Meta:
        model = Project
        fields = ('id', 'name', 'pms', 'autoregister', 'platform')


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('id', 'name', 'project')


class ServerPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServerProperty
        fields = ('id', 'prefix', 'name', 'kind', 'enabled')


class ClientPropertySerializer(serializers.ModelSerializer):
    code = serializers.CharField(allow_blank=False)

    class Meta:
        model = ClientProperty
        fields = ('id', 'prefix', 'name', 'kind', 'enabled', 'language', 'code')


class AttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = ('id',)


class ServerAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServerAttribute
        fields = ('id', 'property_att', 'value', 'description')


class ClientAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientAttribute
        fields = ('id', 'property_att', 'value', 'description')


class ScheduleDelaySerializer(serializers.ModelSerializer):
    attributes = AttributeSerializer(many=True)

    class Meta:
        model = ScheduleDelay
        fields = ('id', 'delay', 'attributes')


class ScheduleSerializer(serializers.ModelSerializer):
    delays = ScheduleDelaySerializer(many=True)

    class Meta:
        model = Schedule
        fields = ('id', 'name', 'description', 'delays')


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
            'project': obj.project.id,
            'store': obj.store.id
        }

    def create(self, validated_data):
        file_list = validated_data['files']
        if type(file_list) != 'list':
            file_list = [file_list]  # always mutiple files

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


class RepositorySerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(read_only=True)

    def create(self, validated_data):
        _repo = super(RepositorySerializer, self).create(validated_data)
        Repository.create_repository_metadata(_repo.id)
        return _repo

    def update(self, instance, validated_data):
        _old_obj = self.Meta.model.objects.get(id=instance.id)
        _old_pkgs = sorted(_old_obj.available_packages.values_list('id', flat=True))
        _old_name = _old_obj.name

        #https://github.com/tomchristie/django-rest-framework/issues/2442
        instance = super(RepositorySerializer, self).update(
            instance, validated_data
        )
        _new_pkgs = sorted(instance.available_packages.values_list('id', flat=True))

        if cmp(_old_pkgs, _new_pkgs) != 0 or _old_name != validated_data['name']:
            Repository.create_repository_metadata(instance.id)

            if _old_name != validated_data['name']:
                Repository.remove_repository_metadata(
                    instance.id, _old_obj.slug
                )

        return instance

    def validate(self, data):
        for item in data.get('available_packages'):
            if item.project.id != data['project'].id:
                raise serializers.ValidationError(
                    _('Package %s must belong to the project %s') % (
                        item, data['project']
                    )
                )

        return data

    class Meta:
        model = Repository
        fields = (
            'id', 'name', 'slug', 'enabled', 'project', 'comment',
            'available_packages', 'packages_to_install', 'packages_to_remove',
            'included_attributes', 'excluded_attributes',
            'start_date', 'schedule',
            'default_preincluded_packages', 'default_included_packages',
            'default_excluded_packages'
        )
