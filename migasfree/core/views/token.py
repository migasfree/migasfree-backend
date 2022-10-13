# -*- coding: utf-8 *-*

# Copyright (c) 2015-2022 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2022 Alberto Gacías <alberto@migasfree.org>
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

from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Prefetch
from django.http import HttpResponse, QueryDict
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.utils.translation import gettext
from django_redis import get_redis_connection
from rest_framework import (
    viewsets, parsers, status,
    mixins, permissions,
)
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...app_catalog.resources import (
    ApplicationResource, CategoryResource, PolicyResource,
)
from ...client.models import Computer
from ...client.resources import (
    ComputerResource, UserResource, FaultDefinitionResource,
    ErrorResource, FaultResource, MigrationResource,
    StatusLogResource, SynchronizationResource, NotificationResource,
    PackageHistoryResource,
)
from ...client.serializers import ComputerInfoSerializer
from ...device.models import Logical
from ...device.serializers import LogicalSerializer
from ...device.resources import (
    CapabilityResource, ConnectionResource, DeviceResource, DriverResource,
    ManufacturerResource, ModelResource, LogicalResource, TypeResource,
)
from ...mixins import DatabaseCheckMixin
from ...utils import save_tempfile

from .. import tasks
from ..resources import (
    ClientAttributeResource, ServerAttributeResource,
    ClientPropertyResource, ServerPropertyResource,
    ProjectResource, PlatformResource, AttributeSetResource,
    UserProfileResource, GroupResource, DomainResource, ScopeResource,
    DeploymentResource, ScheduleResource, StoreResource, PackageResource,
    PackageSetResource,
)
from ..models import (
    Platform, Project, Store,
    ServerProperty, ClientProperty,
    ServerAttribute, ClientAttribute, Attribute,
    Schedule, ScheduleDelay,
    Package, PackageSet, Deployment,
    ExternalSource, InternalSource,
    Domain, Scope, UserProfile,
    AttributeSet, Property,
)
from ..serializers import (
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
from ..filters import (
    DeploymentFilter, PackageFilter, ProjectFilter, StoreFilter,
    ClientAttributeFilter, ServerAttributeFilter, ScheduleDelayFilter,
    AttributeSetFilter, PropertyFilter, AttributeFilter, PlatformFilter,
    UserProfileFilter, PermissionFilter, GroupFilter, DomainFilter,
    ScopeFilter, ScheduleFilter, PackageSetFilter, ClientPropertyFilter,
)


class ExportViewSet(viewsets.ViewSet):
    @action(methods=['get'], detail=False)
    def export(self, request):
        exceptions = {
            'attributeset': 'AttributeSet',
            'clientattribute': 'ClientAttribute',
            'serverattribute': 'ServerAttribute',
            'clientproperty': 'ClientProperty',
            'serverproperty': 'ServerProperty',
            'faultdefinition': 'FaultDefinition',
            'packagehistory': 'PackageHistory',
            'packageset': 'PackageSet',
            'statuslog': 'StatusLog',
            'userprofile': 'UserProfile',
        }

        class_name = self.basename.capitalize()
        if class_name.lower() in exceptions:
            class_name = exceptions[class_name.lower()]

        resource = globals()[f'{class_name}Resource']
        obj = resource()
        data = obj.export(
            self.filter_queryset(self.get_queryset())
        )

        response = HttpResponse(
            data.csv,
            status=status.HTTP_200_OK,
            content_type='text/csv',
        )
        response['Content-Disposition'] = f'attachment; filename="{self.basename}.csv"'

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
class AttributeSetViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
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
class PlatformViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
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
class ProjectViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
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

    def create(self, request, *args, **kwargs):
        data = dict(request.data)

        slug = slugify(data['name'])
        if Project.objects.filter(slug=slug).exists():
            return Response(
                {'detail': gettext('Project slug already exists')},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().create(request, *args, **kwargs)


@permission_classes((permissions.DjangoModelPermissions,))
class StoreViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
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
class PropertyViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
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
class ServerPropertyViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = ServerProperty.objects.filter(sort='server')
    serializer_class = ServerPropertySerializer
    filterset_class = PropertyFilter
    search_fields = ['name', 'prefix']


@permission_classes((permissions.DjangoModelPermissions,))
class ClientPropertyViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = ClientProperty.objects.filter(sort__in=['client', 'basic'])
    serializer_class = ClientPropertySerializer
    filterset_class = ClientPropertyFilter
    search_fields = ['name', 'prefix']


@permission_classes((permissions.DjangoModelPermissions,))
class AttributeViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Attribute.objects.all()
    serializer_class = AttributeSerializer
    filterset_class = AttributeFilter
    search_fields = ['value', 'description']

    def get_queryset(self):
        if self.request is None:
            return Attribute.objects.none()

        return Attribute.objects.scope(self.request.user.userprofile)


@permission_classes((permissions.DjangoModelPermissions,))
class ServerAttributeViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
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
            serializer_computers = ComputerInfoSerializer(
                computers,
                context={'request': request},
                many=True, read_only=True
            )

            inflicted = Computer.productive.filter(
                sync_attributes__in=[tag]
            ).exclude(tags__in=[tag])
            serializer_inflicted = ComputerInfoSerializer(
                inflicted,
                context={'request': request},
                many=True, read_only=True
            )

            return Response(
                {
                    'computers': serializer_computers.data,
                    'inflicted': serializer_inflicted.data
                },
                status=status.HTTP_200_OK
            )

        if request.method == 'PATCH':
            computers = request.data.get('computers', [])
            tag.update_computers(computers)

            return Response(status=status.HTTP_204_NO_CONTENT)


@permission_classes((permissions.DjangoModelPermissions,))
class ClientAttributeViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
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
class ScheduleDelayViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet):
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
class ScheduleViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
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
        DatabaseCheckMixin,
        mixins.CreateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.DestroyModelMixin,
        mixins.ListModelMixin,
        viewsets.GenericViewSet,
        MigasViewSet,
        ExportViewSet
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

        if not data['name']:
            package_path = save_tempfile(data['files'][0])
            response = tasks.package_metadata.apply_async(
                kwargs={
                    'pms_name': store.project.pms,
                    'package': package_path
                },
                queue=f'pms-{store.project.pms}'
            ).get()
            os.remove(package_path)
            if response['name']:
                data['name'] = response['name']
                data['version'] = response['version']
                data['architecture'] = response['architecture']

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

        response = tasks.package_info.apply_async(
            kwargs={
                'pms_name': obj.project.pms,
                'package': Package.path(obj.project.slug, obj.store.slug, obj.fullname)
            },
            queue=f'pms-{obj.project.pms}'
        ).get()

        return Response({'data': response}, status=status.HTTP_200_OK)


@permission_classes((permissions.DjangoModelPermissions,))
class PackageSetViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
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
            if not name:
                package_path = save_tempfile(file_)
                response = tasks.package_metadata.apply_async(
                    kwargs={
                        'pms_name': project.pms,
                        'package': package_path
                    },
                    queue=f'pms-{project.pms}'
                ).get()
                os.remove(package_path)
                if response['name']:
                    name = response['name']
                    version = response['version']
                    architecture = response['architecture']

            if not name or not version or not architecture:
                return {
                    'error': gettext('Package %s has an incorrect name format') % file_.name
                }

            try:
                pkg = Package.objects.create(
                    fullname=file_.name,
                    name=name, version=version, architecture=architecture,
                    project=project,
                    store=store,
                    file_=file_
                )
            except IntegrityError:
                return {
                    'error': gettext('Package %s is duplicated in store %s') % (file_.name, store.name)
                }

            new_pkgs.append(str(pkg.id))

        return new_pkgs

    def create(self, request, *args, **kwargs):
        files = request.data.getlist('files')
        if files:
            project_id = request.data.get('project', 0)
            store_id = request.data.get('store', 0)

            project = Project.objects.get(id=project_id)
            store = Store.objects.get(id=store_id)

            if project and store:
                packages = request.data.getlist('packages', [])
                packages = list(filter(None, packages))
                upload_packages = self._upload_packages(project, store, files)
                if isinstance(upload_packages, dict):
                    return Response(upload_packages, status=status.HTTP_400_BAD_REQUEST)
                packages.extend(upload_packages)
                request.data.setlist('packages', packages)

        return super().create(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        obj = self.get_object()

        files = request.data.getlist('files')
        if files:
            packages = request.data.getlist('packages', [])
            packages = list(filter(None, packages))
            upload_packages = self._upload_packages(obj.project, obj.store, files)
            if isinstance(upload_packages, dict):
                return Response(upload_packages, status=status.HTTP_400_BAD_REQUEST)
            packages.extend(upload_packages)
            request.data.setlist('packages', packages)

        return super().partial_update(request, *args, **kwargs)


@permission_classes((permissions.DjangoModelPermissions,))
class DeploymentViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
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
class InternalSourceViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet):
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
        deploy = self.get_object()
        tasks.create_repository_metadata.apply_async(
            queue=f'pms-{deploy.pms().name}',
            kwargs={'deployment_id': deploy.id}
        )

        return Response(
            {'detail': gettext('Operation received')},
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False)
    def generating(self, request):
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
class ExternalSourceViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet):
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
class UserProfileViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
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
    def domain_admins(self, request):
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

    @action(methods=['post'], detail=True, url_path='update-token')
    def set_token(self, request, pk=None):
        user = self.get_object()
        token = user.update_token()

        return Response(
            {
                'detail': gettext('Token updated!'),
                'info': token
            },
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
class GroupViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, ExportViewSet):
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
class PermissionViewSet(DatabaseCheckMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    filterset_class = PermissionFilter
    search_fields = ['name']


@permission_classes((permissions.DjangoModelPermissions,))
class DomainViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
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
class ScopeViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
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

        filter_by_user = True
        if self.action == 'list':
            filter_by_user = not (self.request.user.userprofile.is_superuser and self.request.GET.get('page', 0))
        else:
            filter_by_user = not self.request.user.userprofile.is_superuser

        qs = Scope.objects.scope(self.request.user.userprofile, filter_by_user)
        if self.action == 'list':
            return qs

        qs_att = Attribute.objects.scope(self.request.user.userprofile)

        return qs.prefetch_related(
            Prefetch('included_attributes', queryset=qs_att),
            'included_attributes__property_att',
            Prefetch('excluded_attributes', queryset=qs_att),
            'excluded_attributes__property_att'
        )
