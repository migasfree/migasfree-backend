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
Package serializers.
"""

from django.utils.text import slugify
from rest_framework import serializers

from ..models import Package, PackageSet, Project, Store
from ..pms import get_available_mimetypes
from ..validators import MimetypeValidator
from .platform import ProjectInfoSerializer
from .store import StoreInfoSerializer


class PackageInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ('id', 'fullname')


class PackageSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    store = serializers.PrimaryKeyRelatedField(queryset=Store.objects.all())
    files = serializers.FileField(allow_empty_file=False, validators=[MimetypeValidator(get_available_mimetypes())])
    fullname = serializers.CharField(max_length=170, required=False, allow_blank=True)

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
            'store': {'id': obj.store.id if obj.store else 0, 'name': obj.store.name if obj.store else ''},
            'url': obj.url(),
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
            file_=file_,
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
