# -*- coding: utf-8 *-*

# Copyright (c) 2015-2019 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2019 Alberto Gacías <alberto@migasfree.org>
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

from urllib.request import urlopen, URLError, HTTPError
from wsgiref.util import FileWrapper

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext
from django_redis import get_redis_connection
from rest_framework import (
    viewsets, parsers, status,
    mixins, views, filters,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_filters import backends

from .mixins import SafeConnectionMixin

from migasfree.device.models import Logical
from migasfree.device.serializers import LogicalSerializer

from ..utils import read_remote_chunks
from .models import (
    Platform, Project, Store,
    ServerProperty, ClientProperty,
    ServerAttribute, ClientAttribute,
    Schedule, ScheduleDelay,
    Package, Deployment,
    ExternalSource, InternalSource,
    Domain, Scope,
    AttributeSet, Property,
)
from .serializers import (
    PlatformSerializer, ProjectSerializer, ProjectWriteSerializer,
    StoreSerializer, StoreWriteSerializer,
    ServerPropertySerializer, ClientPropertySerializer,
    ServerAttributeSerializer, ServerAttributeWriteSerializer,
    ClientAttributeSerializer, ClientAttributeWriteSerializer,
    ScheduleSerializer, ScheduleWriteSerializer,
    ScheduleDelaySerializer, ScheduleDelayWriteSerializer,
    PackageSerializer, DeploymentSerializer,
    DomainWriteSerializer, DomainSerializer,
    ScopeSerializer, ScopeWriteSerializer,
    AttributeSetSerializer, AttributeSetWriteSerializer,
    PropertySerializer, PropertyWriteSerializer,
    ExternalSourceSerializer, ExternalSourceWriteSerializer,
    InternalSourceSerializer, InternalSourceWriteSerializer,
)
from .filters import (
    DeploymentFilter, PackageFilter, ProjectFilter, StoreFilter,
    ClientAttributeFilter, ServerAttributeFilter, ScheduleDelayFilter,
    AttributeSetFilter, PropertyFilter,
)

from . import tasks


class SafePackagerConnectionMixin(SafeConnectionMixin):
    decrypt_key = settings.MIGASFREE_PRIVATE_KEY
    verify_key = settings.MIGASFREE_PACKAGER_PUB_KEY

    sign_key = settings.MIGASFREE_PRIVATE_KEY
    encrypt_key = settings.MIGASFREE_PACKAGER_PUB_KEY


class AttributeSetViewSet(viewsets.ModelViewSet):
    queryset = AttributeSet.objects.all()
    serializer_class = AttributeSetSerializer
    filter_class = AttributeSetFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend, filters.SearchFilter)
    search_fields = ['value', 'description']
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return AttributeSetWriteSerializer

        return AttributeSetSerializer


class PlatformViewSet(viewsets.ModelViewSet):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_queryset(self):
        user = self.request.user.userprofile
        qs = self.queryset
        if not user.is_view_all():
            qs = qs.filter(project__in=user.get_projects()).distinct()

        return qs


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    filter_class = ProjectFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return ProjectWriteSerializer

        return ProjectSerializer

    def get_queryset(self):
        user = self.request.user.userprofile
        qs = self.queryset
        if not user.is_view_all():
            qs = qs.filter(id__in=user.get_projects())

        return qs


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    filter_class = StoreFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend, filters.SearchFilter)
    search_fields = ['name']
    ordering_fields = '__all__'
    ordering = ('name', 'project__name')

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return StoreWriteSerializer

        return StoreSerializer

    def get_queryset(self):
        user = self.request.user.userprofile
        qs = self.queryset
        if not user.is_view_all():
            qs = qs.filter(project__in=user.get_projects())

        return qs


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    filter_class = PropertyFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend, filters.SearchFilter)
    search_fields = ['name', 'language', 'code']
    ordering_fields = '__all__'
    ordering = ('prefix', 'name')

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return PropertyWriteSerializer

        return PropertySerializer


class ServerPropertyViewSet(viewsets.ModelViewSet):
    queryset = ServerProperty.objects.filter(sort='server')
    serializer_class = ServerPropertySerializer


class ClientPropertyViewSet(viewsets.ModelViewSet):
    queryset = ClientProperty.objects.filter(sort='client')
    serializer_class = ClientPropertySerializer


class ServerAttributeViewSet(viewsets.ModelViewSet):
    queryset = ServerAttribute.objects.filter(property_att__sort='server')
    serializer_class = ServerAttributeSerializer
    filter_class = ServerAttributeFilter

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return ServerAttributeWriteSerializer

        return ServerAttributeSerializer


class ClientAttributeViewSet(viewsets.ModelViewSet):
    queryset = ClientAttribute.objects.filter(property_att__sort='client')
    serializer_class = ClientAttributeSerializer
    filter_class = ClientAttributeFilter

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return ClientAttributeWriteSerializer

        return ClientAttributeSerializer

    def get_queryset(self):
        user = self.request.user.userprofile
        qs = self.queryset
        if not user.is_view_all():
            qs = qs.filter(id__in=user.get_attributes()).distinct()

        return qs

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

        attribute = get_object_or_404(ClientAttribute, pk=pk)
        logical_devices = attribute.devicelogical_set.all()

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


class ScheduleDelayViewSet(viewsets.ModelViewSet):
    queryset = ScheduleDelay.objects.all()
    serializer_class = ScheduleDelaySerializer
    filter_class = ScheduleDelayFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)
    ordering_fields = '__all__'
    ordering = ('delay',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return ScheduleDelayWriteSerializer

        return ScheduleDelaySerializer


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return ScheduleWriteSerializer

        return ScheduleSerializer


class PackageViewSet(
        mixins.CreateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.DestroyModelMixin,
        mixins.ListModelMixin,
        viewsets.GenericViewSet
):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    filter_class = PackageFilter
    parser_classes = (parsers.MultiPartParser, parsers.FormParser,)
    ordering = ('name', 'project__name')

    def get_queryset(self):
        user = self.request.user.userprofile
        qs = self.queryset
        if not user.is_view_all():
            qs = qs.filter(project__in=user.get_projects())

        return qs

    @action(methods=['get'], detail=False)
    def orphan(self, request):
        """
        Returns packages that are not in any deployment
        """
        serializer = PackageSerializer(
            Package.objects.filter(deployment__id=None),
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class InternalSourceViewSet(viewsets.ModelViewSet):
    queryset = InternalSource.objects.all()
    serializer_class = InternalSourceSerializer
    filter_class = DeploymentFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)
    ordering_fields = '__all__'
    ordering = ('-start_date', 'name')

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return InternalSourceWriteSerializer

        return InternalSourceSerializer

    def get_queryset(self):
        user = self.request.user.userprofile
        qs = self.queryset.filter(source=Deployment.SOURCE_INTERNAL)
        if not user.is_view_all():
            qs = qs.filter(project__in=user.get_projects())
            if user.domain_preference:
                qs = qs.filter(domain=user.domain_preference)

        return qs

    @action(methods=['get'], detail=True)
    def metadata(self, request, pk=None):
        get_object_or_404(InternalSource, pk=pk)
        tasks.create_repository_metadata.delay(pk)

        return Response(
            {'detail': ugettext('Operation received')},
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


class ExternalSourceViewSet(viewsets.ModelViewSet):
    queryset = ExternalSource.objects.all()
    serializer_class = ExternalSourceSerializer
    filter_class = DeploymentFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)
    ordering_fields = '__all__'
    ordering = ('-start_date', 'name')

    def get_queryset(self):
        user = self.request.user.userprofile
        qs = self.queryset.filter(source=Deployment.SOURCE_EXTERNAL)
        if not user.is_view_all():
            qs = qs.filter(project__in=user.get_projects())
            if user.domain_preference:
                qs = qs.filter(domain=user.domain_preference)

        return qs

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return ExternalSourceWriteSerializer

        return ExternalSourceSerializer


class DomainViewSet(viewsets.ModelViewSet):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return DomainWriteSerializer

        return DomainSerializer


class ScopeViewSet(viewsets.ModelViewSet):
    queryset = Scope.objects.all()
    serializer_class = ScopeSerializer
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return ScopeWriteSerializer

        return ScopeSerializer


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
            package = Package.objects.filter(name=_file.name, project=project)
            if package:
                package[0].update_store(store)
            else:
                Package.objects.create(
                    name=_file.name,
                    project=project,
                    store=store,
                    file_list=[_file]
                )

        target = Package.path(project.slug, store.slug, _file.name)
        Package.handle_uploaded_file(_file, target)

        return Response(
            self.create_response(ugettext('Data received')),
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
            name=packageset, project=project
        )
        if package:
            package[0].update_store(store)
        else:
            Package.objects.create(
                name=packageset,
                project=project,
                store=store,
                file_list=[_file]
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
            self.create_response(ugettext('Data received')),
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
                self.create_response(ugettext('Malformed claims')),
                status=status.HTTP_400_BAD_REQUEST
            )

        project = get_object_or_404(Project, name=claims.get('project'))
        package = get_object_or_404(
            Package,
            name=os.path.basename(claims.get('packageset')),
            project=project
        )

        deployments = Deployment.objects.filter(
            available_packages__id=package.id
        )
        for deploy in deployments:
            tasks.create_repository_metadata.delay(deploy.id)

        return Response(
            self.create_response(ugettext('Data received')),
            status=status.HTTP_200_OK
        )


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

            url = u'{}/{}'.format(source.base_url, resource)

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
                    u'HTTP Error: {} {}'.format(e.code, url),
                    status=e.code
                )
            except URLError as e:
                return HttpResponse(
                    u'URL Error: {} {}'.format(e.reason, url),
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            if not os.path.isfile(_file_local):
                return HttpResponse(status=status.HTTP_204_NO_CONTENT)
            else:
                response = HttpResponse(FileWrapper(open(_file_local, 'rb')), content_type='application/octet-stream')
                response['Content-Disposition'] = u'attachment; filename={}'.format(os.path.basename(_file_local))
                response['Content-Length'] = os.path.getsize(_file_local)

                return response
