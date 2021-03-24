# -*- coding: utf-8 *-*

# Copyright (c) 2015-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2021 Alberto Gacías <alberto@migasfree.org>
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

import os
import time
import ssl

from urllib.error import URLError, HTTPError
from urllib.request import urlopen
from wsgiref.util import FileWrapper

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext
from django_redis import get_redis_connection
from rest_framework import (
    viewsets, parsers, status,
    mixins, views, permissions,
)
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from .mixins import SafeConnectionMixin

from ..client.models import Computer
from ..client.resources import (
    ComputerResource, UserResource,
    ErrorResource, FaultResource, MigrationResource,
    StatusLogResource, SynchronizationResource,
)
from ..client.serializers import ComputerInfoSerializer
from .resources import (
    ClientAttributeResource, ServerAttributeResource,
    ClientPropertyResource, ServerPropertyResource,
    ProjectResource,
)
from ..device.models import Logical
from ..device.serializers import LogicalSerializer
from ..utils import read_remote_chunks

from .pms import get_available_pms

from .models import (
    Platform, Project, Store,
    ServerProperty, ClientProperty,
    ServerAttribute, ClientAttribute, Attribute,
    Schedule, ScheduleDelay,
    Package, PackageSet, Deployment,
    ExternalSource, InternalSource,
    Domain, Scope, UserProfile,
    AttributeSet, Property,
)
from .serializers import (
    PlatformSerializer, ProjectSerializer, ProjectWriteSerializer,
    StoreSerializer, StoreWriteSerializer,
    ServerPropertySerializer, ClientPropertySerializer,
    ServerAttributeSerializer, ServerAttributeWriteSerializer,
    ClientAttributeSerializer, ClientAttributeWriteSerializer,
    AttributeSerializer,
    ScheduleSerializer, ScheduleWriteSerializer,
    ScheduleDelaySerializer, ScheduleDelayWriteSerializer,
    PackageSerializer, PackageSetSerializer, PackageSetWriteSerializer,
    DeploymentSerializer, DeploymentWriteSerializer, DeploymentListSerializer,
    DomainWriteSerializer, DomainSerializer, DomainListSerializer,
    ScopeSerializer, ScopeWriteSerializer, ScopeListSerializer,
    UserProfileSerializer, UserProfileWriteSerializer,
    ChangePasswordSerializer, UserProfileListSerializer,
    GroupSerializer, GroupWriteSerializer, PermissionSerializer,
    AttributeSetSerializer, AttributeSetWriteSerializer,
    PropertySerializer, PropertyWriteSerializer,
    ExternalSourceSerializer, ExternalSourceWriteSerializer,
    InternalSourceSerializer, InternalSourceWriteSerializer,
)
from .filters import (
    DeploymentFilter, PackageFilter, ProjectFilter, StoreFilter,
    ClientAttributeFilter, ServerAttributeFilter, ScheduleDelayFilter,
    AttributeSetFilter, PropertyFilter, AttributeFilter, PlatformFilter,
    UserProfileFilter, PermissionFilter, GroupFilter, DomainFilter,
    ScopeFilter, ScheduleFilter, PackageSetFilter,
)

from . import tasks


class SafePackagerConnectionMixin(SafeConnectionMixin):
    decrypt_key = settings.MIGASFREE_PRIVATE_KEY
    verify_key = settings.MIGASFREE_PACKAGER_PUB_KEY

    sign_key = settings.MIGASFREE_PRIVATE_KEY
    encrypt_key = settings.MIGASFREE_PACKAGER_PUB_KEY


class ExportViewSet(viewsets.ViewSet):
    @action(methods=['get'], detail=False)
    def export(self, request, format=None):
        class_name = self.basename.capitalize()
        if class_name.lower() == 'clientattribute':
            class_name = 'ClientAttribute'
        if class_name.lower() == 'serverattribute':
            class_name = 'ServerAttribute'
        if class_name.lower() == 'clientproperty':
            class_name = 'ClientProperty'
        if class_name.lower() == 'serverproperty':
            class_name = 'ServerProperty'
        if class_name.lower() == 'statuslog':
            class_name = 'StatusLog'

        resource = globals()['{}Resource'.format(class_name)]
        obj = resource()
        data = obj.export(
            self.filter_queryset(self.get_queryset())
        )

        response = HttpResponse(
            data.csv,
            status=status.HTTP_200_OK,
            content_type='text/csv',
        )
        response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(self.basename)

        return response


class MigasViewSet(viewsets.ViewSet):
    @action(methods=['get'], detail=True)
    def relations(self, request, pk=None):
        app = self.queryset.model._meta.app_label
        model = self.queryset.model._meta.model_name

        try:
            response = apps.get_model(app, model).objects.get(pk=pk).relations(request)

            return Response(response, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @action(methods=['get'], detail=True)
    def badge(self, request, pk=None):
        app = self.queryset.model._meta.app_label
        model = self.queryset.model._meta.model_name

        try:
            response = apps.get_model(app, model).objects.get(pk=pk).badge()

            return Response(response, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


@permission_classes((permissions.DjangoModelPermissions,))
class AttributeSetViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = AttributeSet.objects.all()
    serializer_class = AttributeSetSerializer
    filterset_class = AttributeSetFilter
    search_fields = ['name', 'description']
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return AttributeSetWriteSerializer

        return AttributeSetSerializer

    def get_queryset(self):
        if self.request is None:
            return AttributeSet.objects.none()

        qs = Attribute.objects.scope(self.request.user.userprofile)

        return AttributeSet.objects.scope(
            self.request.user.userprofile
        ).prefetch_related(
            Prefetch('included_attributes', queryset=qs),
            Prefetch('excluded_attributes', queryset=qs),
            'included_attributes__property_att',
            'excluded_attributes__property_att',
        )


@permission_classes((permissions.DjangoModelPermissions,))
class PlatformViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    filterset_class = PlatformFilter
    ordering_fields = '__all__'
    ordering = ('name',)
    search_fields = ['name']

    def get_queryset(self):
        if self.request is None:
            return Platform.objects.none()

        return Platform.objects.scope(self.request.user.userprofile)


@permission_classes((permissions.DjangoModelPermissions,))
class ProjectViewSet(viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    filterset_class = ProjectFilter
    ordering_fields = '__all__'
    ordering = ('name',)
    search_fields = ['name']

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return ProjectWriteSerializer

        return ProjectSerializer

    def get_queryset(self):
        if self.request is None:
            return Project.objects.none()

        return Project.objects.scope(self.request.user.userprofile)


@permission_classes((permissions.DjangoModelPermissions,))
class StoreViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    filterset_class = StoreFilter
    ordering_fields = '__all__'
    ordering = ('name', 'project__name')
    search_fields = ['name']

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return StoreWriteSerializer

        return StoreSerializer

    def get_queryset(self):
        if self.request is None:
            return Store.objects.none()

        return Store.objects.scope(self.request.user.userprofile)


@permission_classes((permissions.DjangoModelPermissions,))
class PropertyViewSet(viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    filterset_class = PropertyFilter
    ordering_fields = '__all__'
    ordering = ('prefix', 'name')
    search_fields = ['name', 'language', 'code']

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return PropertyWriteSerializer

        return PropertySerializer

    @action(methods=['get'], detail=False)
    def kind(self, request):
        """
        Returns kind definition
        """

        return Response(
            dict(Property.KIND_CHOICES),
            status=status.HTTP_200_OK
        )


@permission_classes((permissions.DjangoModelPermissions,))
class ServerPropertyViewSet(viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = ServerProperty.objects.filter(sort='server')
    serializer_class = ServerPropertySerializer
    filterset_class = PropertyFilter
    search_fields = ['name', 'prefix']


@permission_classes((permissions.DjangoModelPermissions,))
class ClientPropertyViewSet(viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = ClientProperty.objects.filter(sort__in=['client', 'basic'])
    serializer_class = ClientPropertySerializer
    filterset_class = PropertyFilter
    search_fields = ['name', 'prefix']


@permission_classes((permissions.DjangoModelPermissions,))
class AttributeViewSet(viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Attribute.objects.all()
    serializer_class = AttributeSerializer
    filterset_class = AttributeFilter
    search_fields = ['value', 'description']

    def get_queryset(self):
        if self.request is None:
            return Attribute.objects.none()

        return Attribute.objects.scope(self.request.user.userprofile)


@permission_classes((permissions.DjangoModelPermissions,))
class ServerAttributeViewSet(viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = ServerAttribute.objects.filter(property_att__sort='server')
    serializer_class = ServerAttributeSerializer
    filterset_class = ServerAttributeFilter
    search_fields = ['value', 'description']

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return ServerAttributeWriteSerializer

        return ServerAttributeSerializer

    def get_queryset(self):
        if self.request is None:
            return ServerAttribute.objects.none()

        return ServerAttribute.objects.scope(self.request.user.userprofile)

    @action(methods=['get', 'patch'], detail=True)
    def computers(self, request, pk=None):
        tag = self.get_object()

        if request.method == 'GET':
            computers = Computer.productive.scope(
                request.user.userprofile
            ).filter(tags__in=[tag])
            serializerComputers = ComputerInfoSerializer(
                computers,
                context={'request': request},
                many=True, read_only=True
            )

            inflicted = Computer.productive.filter(
                sync_attributes__in=[tag]
            ).exclude(tags__in=[tag])
            serializerInflicted = ComputerInfoSerializer(
                inflicted,
                context={'request': request},
                many=True, read_only=True
            )

            return Response(
                {
                    'computers': serializerComputers.data,
                    'inflicted': serializerInflicted.data
                },
                status=status.HTTP_200_OK
            )

        if request.method == 'PATCH':
            computers = request.data.get('computers', [])
            tag.update_computers(computers)

            return Response(status=status.HTTP_204_NO_CONTENT)


@permission_classes((permissions.DjangoModelPermissions,))
class ClientAttributeViewSet(viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = ClientAttribute.objects.filter(property_att__sort__in=['client', 'basic'])
    serializer_class = ClientAttributeSerializer
    filterset_class = ClientAttributeFilter
    search_fields = ['value', 'description']

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return ClientAttributeWriteSerializer

        return ClientAttributeSerializer

    def get_queryset(self):
        if self.request is None:
            return ClientAttribute.objects.none()

        return ClientAttribute.objects.scope(self.request.user.userprofile)

    @action(methods=['get', 'put', 'patch'], detail=True, url_path='logical-devices')
    def logical_devices(self, request, pk=None):
        """
        GET
            returns: [
                {
                    "id": 112,
                    "device": {
                        "id": 6,
                        "name": "19940"
                    },
                    "feature": {
                        "id": 2,
                        "name": "Color"
                    },
                    "name": ""
                },
                {
                    "id": 7,
                    "device": {
                        "id": 6,
                        "name": "19940"
                    },
                    "feature": {
                        "id": 1,
                        "name": "BN"
                    },
                    "name": ""
                }
            ]

        PUT, PATCH
            input: [id1, id2, idN]

            returns: status code 201
        """

        attribute = self.get_object()
        logical_devices = attribute.logical_set.all()

        if request.method == 'GET':
            serializer = LogicalSerializer(
                logical_devices,
                many=True
            )

            return Response(serializer.data, status=status.HTTP_200_OK)

        if request.method == 'PATCH':  # append cid attribute to logical devices
            for device_id in request.data:
                device = get_object_or_404(Logical, pk=device_id)
                if device not in logical_devices:
                    device.attributes.add(pk)

            return Response(status=status.HTTP_201_CREATED)

        if request.method == 'PUT':  # replace cid attribute in logical devices
            for device in logical_devices:
                if device in logical_devices:
                    device.attributes.remove(pk)

            for device_id in request.data:
                device = get_object_or_404(Logical, pk=device_id)
                device.attributes.add(pk)

            return Response(status=status.HTTP_201_CREATED)


@permission_classes((permissions.DjangoModelPermissions,))
class ScheduleDelayViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = ScheduleDelay.objects.all()
    serializer_class = ScheduleDelaySerializer
    filterset_class = ScheduleDelayFilter
    ordering_fields = '__all__'
    ordering = ('delay',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return ScheduleDelayWriteSerializer

        return ScheduleDelaySerializer

    def get_queryset(self):
        if self.request is None:
            return ScheduleDelay.objects.none()

        qs = Attribute.objects.scope(self.request.user.userprofile)

        return ScheduleDelay.objects.scope(
            self.request.user.userprofile
        ).prefetch_related(
            Prefetch('attributes', queryset=qs),
            'attributes__property_att', 'schedule'
        )


@permission_classes((permissions.DjangoModelPermissions,))
class ScheduleViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    filterset_class = ScheduleFilter
    search_fields = ['name']
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return ScheduleWriteSerializer

        return ScheduleSerializer

    def get_queryset(self):
        if self.request is None:
            return Schedule.objects.none()

        return self.queryset.prefetch_related('delays')


@permission_classes((permissions.DjangoModelPermissions,))
class PackageViewSet(
        mixins.CreateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.DestroyModelMixin,
        mixins.ListModelMixin,
        viewsets.GenericViewSet,
        MigasViewSet
):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    filterset_class = PackageFilter
    parser_classes = (parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser)
    ordering_fields = '__all__'
    ordering = ('fullname', 'version', 'project__name')
    search_fields = ['fullname']

    def get_queryset(self):
        if self.request is None:
            return Package.objects.none()

        return Package.objects.scope(self.request.user.userprofile)

    def create(self, request, *args, **kwargs):
        data = dict(request.data)

        if 'fullname' not in data and 'files' in data and len(data['files']) > 0:
            data['fullname'] = data['files'][0].name

        if 'name' not in data:
            data['name'], data['version'], data['architecture'] = Package.normalized_name(data['fullname'])

        store = get_object_or_404(Store, pk=data['store'][0])

        try:
            package = Package.objects.create(
                fullname=data['fullname'],
                name=data['name'],
                version=data['version'],
                architecture=data['architecture'],
                project=store.project,
                store=store,
                file_=data['files'][0]
            )

            serializer = PackageSerializer(package)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response(
                {'detail': gettext('Package already exists')},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(methods=['get'], detail=False)
    def orphan(self, request):
        """
        Returns packages that are not in any deployment
        """
        serializer = PackageSerializer(
            Package.objects.filter(
                deployment__id=None,
                store__isnull=False
            ),
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True)
    def info(self, request, pk=None):
        obj = self.get_object()

        if obj.store is None:
            return Response(
                {
                    'detail': gettext('The package has no store on the server')
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        response = obj.pms().package_info(
            Package.path(obj.project.name, obj.store.name, obj.fullname)
        )

        return Response({'data': response}, status=status.HTTP_200_OK)


@permission_classes((permissions.DjangoModelPermissions,))
class PackageSetViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = PackageSet.objects.all()
    serializer_class = PackageSetSerializer
    filterset_class = PackageSetFilter
    parser_classes = (parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser)
    search_fields = ['name']
    ordering_fields = '__all__'
    ordering = ('project__name', 'name')

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return PackageSetWriteSerializer

        return PackageSetSerializer

    def get_queryset(self):
        if self.request is None:
            return PackageSet.objects.none()

        return PackageSet.objects.scope(self.request.user.userprofile)

    def _upload_packages(self, project, store, files):
        new_pkgs = []
        for file_ in files:
            name, version, architecture = Package.normalized_name(file_.name)
            if not name or not version or not architecture:
                return Response(
                    {
                        'error': gettext('Package %s has an incorrect name format') % file_.name
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                pkg = Package.objects.create(
                    fullname=file_.name,
                    name=name, version=version, architecture=architecture,
                    project=project,
                    store=store,
                    file_=file_
                )
            except IntegrityError:
                return Response(
                    {
                        'error': gettext('Package %s is duplicated in store %s') % (file_.name, obj.store)
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            new_pkgs.append(str(pkg.id))

        return new_pkgs

    def create(self, request):
        files = request.data.getlist('files')
        if files:
            project_id = request.data.get('project', 0)
            store_id = request.data.get('store', 0)

            project = Project.objects.get(id=project_id)
            store = Store.objects.get(id=store_id)

            if project and store:
                packages = request.data.getlist('packages', [])
                packages = list(filter(None, packages))
                packages.extend(self._upload_packages(project, store, files))
                request.data.setlist('packages', packages)

        return super().create(request)

    def partial_update(self, request, pk=None):
        obj = self.get_object()

        files = request.data.getlist('files')
        if files:
            packages = request.data.getlist('packages', [])
            packages = list(filter(None, packages))
            packages.extend(self._upload_packages(obj.project, obj.store, files))
            request.data.setlist('packages', packages)

        return super().partial_update(request, pk)


@permission_classes((permissions.DjangoModelPermissions,))
class DeploymentViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = Deployment.objects.all()
    serializer_class = DeploymentSerializer
    filterset_class = DeploymentFilter
    search_fields = ['name']
    ordering_fields = '__all__'
    ordering = ('-start_date', 'name')

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return DeploymentWriteSerializer

        if self.action == 'list':
            return DeploymentListSerializer

        return DeploymentSerializer

    def get_queryset(self):
        if self.request is None:
            return Deployment.objects.none()

        return Deployment.objects.scope(self.request.user.userprofile)


@permission_classes((permissions.DjangoModelPermissions,))
class InternalSourceViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = InternalSource.objects.all()
    serializer_class = InternalSourceSerializer
    filterset_class = DeploymentFilter
    ordering_fields = '__all__'
    ordering = ('-start_date', 'name')

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return InternalSourceWriteSerializer

        return InternalSourceSerializer

    def get_queryset(self):
        if self.request is None:
            return InternalSource.objects.none()

        return InternalSource.objects.scope(self.request.user.userprofile)

    @action(methods=['get'], detail=True)
    def metadata(self, request, pk=None):
        self.get_object()
        tasks.create_repository_metadata.delay(pk)

        return Response(
            {'detail': gettext('Operation received')},
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False)
    def generating(self, request, format=None):
        con = get_redis_connection()
        result = con.smembers('migasfree:watch:repos')

        serializer = DeploymentSerializer(
            Deployment.objects.filter(pk__in=result),
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


@permission_classes((permissions.DjangoModelPermissions,))
class ExternalSourceViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = ExternalSource.objects.all()
    serializer_class = ExternalSourceSerializer
    filterset_class = DeploymentFilter
    ordering_fields = '__all__'
    ordering = ('-start_date', 'name')

    def get_queryset(self):
        if self.request is None:
            return ExternalSource.objects.none()

        return ExternalSource.objects.scope(self.request.user.userprofile)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return ExternalSourceWriteSerializer

        return ExternalSourceSerializer


@permission_classes((permissions.DjangoModelPermissions,))
class UserProfileViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    filterset_class = UserProfileFilter
    search_fields = ['username', 'first_name', 'last_name']
    ordering_fields = '__all__'
    ordering = ('username',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return UserProfileWriteSerializer

        if self.action == 'list':
            return UserProfileListSerializer

        return UserProfileSerializer

    def get_queryset(self):
        if self.request is None:
            return UserProfile.objects.none()

        return self.queryset.select_related(
            'domain_preference', 'scope_preference'
        ).prefetch_related(
            'domains',
            'groups',
            'user_permissions',
        )

    @action(methods=['get'], detail=False, url_path='domain-admins')
    def domain_admins(self, request, format=None):
        serializer = UserProfileSerializer(
            UserProfile.objects.filter(
                groups__in=[Group.objects.get(name="Domain Admin")]
            ).order_by('username'),
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(
        methods=['put'],
        detail=True,
        serializer_class=ChangePasswordSerializer,
        url_path='change-password'
    )
    def set_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            user.update_password(serializer.validated_data.get('password'))

            return Response(
                {'detail': gettext('Password changed!')},
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


@permission_classes((permissions.DjangoModelPermissions,))
class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    filterset_class = GroupFilter
    search_fields = ['name']
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return GroupWriteSerializer

        return GroupSerializer


@permission_classes((permissions.DjangoModelPermissions,))
class PermissionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    filterset_class = PermissionFilter
    search_fields = ['name']


@permission_classes((permissions.DjangoModelPermissions,))
class DomainViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    filterset_class = DomainFilter
    search_fields = ['name']
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return DomainWriteSerializer

        if self.action == 'list':
            return DomainListSerializer

        return DomainSerializer

    def get_queryset(self):
        if self.request is None:
            return Domain.objects.none()

        if self.action == 'list':
            return self.queryset

        return self.queryset.prefetch_related(
            'included_attributes',
            'included_attributes__property_att',
            'excluded_attributes',
            'excluded_attributes__property_att',
            'tags',
        )


@permission_classes((permissions.DjangoModelPermissions,))
class ScopeViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = Scope.objects.all()
    serializer_class = ScopeSerializer
    filterset_class = ScopeFilter
    search_fields = ['name']
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return ScopeWriteSerializer

        if self.action == 'list':
            return ScopeListSerializer

        return ScopeSerializer

    def get_queryset(self):
        if self.request is None:
            return Scope.objects.none()

        qs = Scope.objects.scope(self.request.user.userprofile)
        if self.action == 'list':
            return qs

        qs_att = Attribute.objects.scope(self.request.user.userprofile)

        return qs.prefetch_related(
            Prefetch('included_attributes', queryset=qs_att),
            'included_attributes__property_att',
            Prefetch('excluded_attributes', queryset=qs_att),
            'excluded_attributes__property_att'
        )


@permission_classes((permissions.AllowAny,))
class SafePackageViewSet(SafePackagerConnectionMixin, viewsets.ViewSet):
    def create(self, request, format=None):
        """
        claims = {
            'project': project_name,
            'store': store_name,
            'is_package': true|false
        }
        """

        claims = self.get_claims(request.data)
        project = get_object_or_404(Project, name=claims.get('project'))

        store, _ = Store.objects.get_or_create(
            name=claims.get('store'),
            project=project
        )

        _file = request.FILES.get('file')

        if claims.get('is_package'):
            package = Package.objects.filter(
                fullname=_file.name,
                project=project
            )
            if package:
                package[0].update_store(store)
            else:
                name, version, architecture = Package.normalized_name(_file.name)
                Package.objects.create(
                    fullname=_file.name,
                    name=name,
                    version=version,
                    architecture=architecture,
                    project=project,
                    store=store,
                    file_=_file
                )

        target = Package.path(project.slug, store.slug, _file.name)
        Package.handle_uploaded_file(_file, target)

        return Response(
            self.create_response(gettext('Data received')),
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=False, url_path='set')
    def packageset(self, request, format=None):
        """
        claims = {
            'project': project_name,
            'store': store_name,
            'packageset': string,
            'path': string
        }
        """

        claims = self.get_claims(request.data)
        project = get_object_or_404(Project, name=claims.get('project'))
        packageset = os.path.basename(claims.get('packageset'))

        store, _ = Store.objects.get_or_create(
            name=claims.get('store'),
            project=project
        )

        _file = request.FILES.get('file')

        target = os.path.join(
            Store.path(project.slug, store.slug),
            packageset,
            _file.name
        )

        package = Package.objects.filter(
            fullname=packageset, project=project
        )
        if package:
            package[0].update_store(store)
        else:
            name, version, architecture = Package.normalized_name(packageset)
            Package.objects.create(
                fullname=packageset,
                name=name,
                version=version,
                architecture=architecture,
                project=project,
                store=store,
                file_=_file
            )

        Package.handle_uploaded_file(_file, target)

        # if exists path move it
        if claims.get('path'):
            dst = os.path.join(
                Store.path(project.slug, store.slug),
                packageset,
                claims.get('path'),
                _file.name
            )
            try:
                os.makedirs(os.path.dirname(dst))
            except OSError:
                pass
            os.rename(target, dst)

        return Response(
            self.create_response(gettext('Data received')),
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=False, url_path='repos')
    def create_repository(self, request, format=None):
        """
        claims = {
            'project': project_name,
            'packageset': name,
        }
        """

        claims = self.get_claims(request.data)
        if not claims or 'project' not in claims or 'packageset' not in claims:
            return Response(
                self.create_response(gettext('Malformed claims')),
                status=status.HTTP_400_BAD_REQUEST
            )

        project = get_object_or_404(Project, name=claims.get('project'))
        package = get_object_or_404(
            Package,
            fullname=os.path.basename(claims.get('packageset')),
            project=project
        )

        deployments = Deployment.objects.filter(
            available_packages__id=package.id
        )
        for deploy in deployments:
            tasks.create_repository_metadata.delay(deploy.id)

        return Response(
            self.create_response(gettext('Data received')),
            status=status.HTTP_200_OK
        )


@permission_classes((permissions.AllowAny,))
class PmsView(views.APIView):
    def get(self, request, format=None):
        """
        Returns available PMS
        """
        return Response(dict(get_available_pms()))


@permission_classes((permissions.AllowAny,))
class ProgrammingLanguagesView(views.APIView):
    def get(self, request, format=None):
        """
        Returns available programming languages (to formulas and faults definitions)
        """
        return Response(dict(settings.MIGASFREE_PROGRAMMING_LANGUAGES))


@permission_classes((permissions.AllowAny,))
class ServerInfoView(views.APIView):
    def post(self, request, format=None):
        """
        Returns server info
        """
        from .. import __version__, __author__, __contact__, __homepage__

        info = {
            'version': __version__,
            'author': __author__,
            'contact': __contact__,
            'homepage': __homepage__,
        }

        return Response(info)


@permission_classes((permissions.AllowAny,))
class GetSourceFileView(views.APIView):
    def get(self, request, format=None):
        source = None

        _path = request.get_full_path()
        project_name = _path.split('/')[2]
        source_name = _path.split('/')[4]
        resource = _path.split('/src/{}/EXTERNAL/{}/'.format(project_name, source_name))[1]

        _file_local = os.path.join(settings.MIGASFREE_PUBLIC_DIR, _path.split('/src/')[1])

        # FIXME PMS dependency
        if not (_file_local.endswith('.deb') or _file_local.endswith('.rpm')):  # is a metadata file
            source = ExternalSource.objects.get(project__name=project_name, name=source_name)

            if not source.frozen:
                # expired metadata
                if os.path.exists(_file_local) and (
                    source.expire <= 0 or
                    (time.time() - os.stat(_file_local).st_mtime) / (60 * source.expire) > 1
                ):
                    os.remove(_file_local)

        if not os.path.exists(_file_local):
            if not os.path.exists(os.path.dirname(_file_local)):
                os.makedirs(os.path.dirname(_file_local))

            if not source:
                source = ExternalSource.objects.get(project__name=project_name, name=source_name)

            url = '{}/{}'.format(source.base_url, resource)

            try:
                ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
                remote_file = urlopen(url, context=ctx)
                stream = read_remote_chunks(_file_local, remote_file)
                response = HttpResponse(
                    stream,
                    status=status.HTTP_206_PARTIAL_CONTENT,
                    content_type='application/octet-stream'
                )
                response['Cache-Control'] = 'no-cache'

                return response
            except HTTPError as e:
                return HttpResponse(
                    'HTTP Error: {} {}'.format(e.code, url),
                    status=e.code
                )
            except URLError as e:
                return HttpResponse(
                    'URL Error: {} {}'.format(e.reason, url),
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            if not os.path.isfile(_file_local):
                return HttpResponse(status=status.HTTP_204_NO_CONTENT)
            else:
                response = HttpResponse(FileWrapper(open(_file_local, 'rb')), content_type='application/octet-stream')
                response['Content-Disposition'] = 'attachment; filename={}'.format(os.path.basename(_file_local))
                response['Content-Length'] = os.path.getsize(_file_local)

                return response
