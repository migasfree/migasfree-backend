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

from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ....client.models import Computer
from ....client.serializers import ComputerInfoSerializer
from ....device.models import Logical
from ....device.serializers import LogicalSerializer
from ....mixins import DatabaseCheckMixin
from ...filters import (
    AttributeFilter,
    AttributeSetFilter,
    ClientAttributeFilter,
    ClientPropertyFilter,
    PropertyFilter,
    ServerAttributeFilter,
    SingularityFilter,
)
from ...models import (
    Attribute,
    AttributeSet,
    ClientAttribute,
    ClientProperty,
    Property,
    ServerAttribute,
    ServerProperty,
    Singularity,
)
from ...serializers import (
    AttributeSerializer,
    AttributeSetSerializer,
    AttributeSetWriteSerializer,
    ClientAttributeSerializer,
    ClientAttributeWriteSerializer,
    ClientPropertySerializer,
    PropertySerializer,
    PropertyWriteSerializer,
    ServerAttributeSerializer,
    ServerAttributeWriteSerializer,
    ServerPropertySerializer,
    SingularitySerializer,
    SingularityWriteSerializer,
)
from .base import ExportViewSet, MigasViewSet


@extend_schema(tags=['singularities'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: name, property_att__name, property_att__prefix',
            type=str,
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class SingularityViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Singularity.objects.all()
    serializer_class = SingularitySerializer
    filterset_class = SingularityFilter
    search_fields = ('name', 'property_att__name', 'property_att__prefix')
    ordering_fields = '__all__'
    ordering = ('property_att__name', '-priority')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return SingularityWriteSerializer

        return SingularitySerializer

    def get_queryset(self):
        if self.request is None:
            return Singularity.objects.none()

        qs = Attribute.objects.scope(self.request.user.userprofile)

        return Singularity.objects.scope(self.request.user.userprofile).prefetch_related(
            Prefetch('included_attributes', queryset=qs),
            Prefetch('excluded_attributes', queryset=qs),
            'included_attributes__property_att',
            'excluded_attributes__property_att',
        )


@extend_schema(tags=['attribute-sets'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: name, description',
            type=str,
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class AttributeSetViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = AttributeSet.objects.all()
    serializer_class = AttributeSetSerializer
    filterset_class = AttributeSetFilter
    search_fields = ('name', 'description')
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return AttributeSetWriteSerializer

        return AttributeSetSerializer

    def get_queryset(self):
        if self.request is None:
            return AttributeSet.objects.none()

        qs = Attribute.objects.scope(self.request.user.userprofile)

        return AttributeSet.objects.scope(self.request.user.userprofile).prefetch_related(
            Prefetch('included_attributes', queryset=qs),
            Prefetch('excluded_attributes', queryset=qs),
            'included_attributes__property_att',
            'excluded_attributes__property_att',
        )


@extend_schema(tags=['properties'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: name, language, code',
            type=str,
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class PropertyViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    filterset_class = PropertyFilter
    ordering_fields = '__all__'
    ordering = ('prefix', 'name')
    search_fields = ('name', 'language', 'code')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return PropertyWriteSerializer

        return PropertySerializer

    @action(methods=['get'], detail=False)
    def kind(self, request):
        """
        Returns kind definition
        """

        return Response(dict(Property.KIND_CHOICES), status=status.HTTP_200_OK)


@extend_schema(tags=['stamps'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: name, prefix',
            type=str,
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class ServerPropertyViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = ServerProperty.objects.filter(sort='server')
    serializer_class = ServerPropertySerializer
    filterset_class = PropertyFilter
    search_fields = ('name', 'prefix')


@extend_schema(tags=['formulas'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: name, prefix',
            type=str,
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class ClientPropertyViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = ClientProperty.objects.filter(sort__in=['client', 'basic'])
    serializer_class = ClientPropertySerializer
    filterset_class = ClientPropertyFilter
    search_fields = ('name', 'prefix')


@extend_schema(tags=['attributes'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: value, description, property_att__prefix',
            type=str,
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class AttributeViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Attribute.objects.all()
    serializer_class = AttributeSerializer
    filterset_class = AttributeFilter
    search_fields = ('value', 'description', 'property_att__prefix')

    def get_queryset(self):
        if self.request is None:
            return Attribute.objects.none()

        return Attribute.objects.scope(self.request.user.userprofile)


@extend_schema(tags=['tags'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: value, description, property_att__prefix',
            type=str,
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class ServerAttributeViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = ServerAttribute.objects.filter(property_att__sort='server')
    serializer_class = ServerAttributeSerializer
    filterset_class = ServerAttributeFilter
    search_fields = ('value', 'description', 'property_att__prefix')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
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
            computers = Computer.productive.scope(request.user.userprofile).filter(tags__in=[tag])
            serializer_computers = ComputerInfoSerializer(
                computers, context={'request': request}, many=True, read_only=True
            )

            inflicted = Computer.productive.filter(sync_attributes__in=[tag]).exclude(tags__in=[tag])
            serializer_inflicted = ComputerInfoSerializer(
                inflicted, context={'request': request}, many=True, read_only=True
            )

            return Response(
                {
                    'computers': serializer_computers.data,
                    'inflicted': serializer_inflicted.data,
                },
                status=status.HTTP_200_OK,
            )

        if request.method == 'PATCH':
            computers = request.data.get('computers', [])
            tag.update_computers(computers)

            return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['features'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: value, description, property_att__prefix',
            type=str,
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class ClientAttributeViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = ClientAttribute.objects.filter(property_att__sort__in=['client', 'basic'])
    serializer_class = ClientAttributeSerializer
    filterset_class = ClientAttributeFilter
    search_fields = ('value', 'description', 'property_att__prefix')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
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
            serializer = LogicalSerializer(logical_devices, many=True)

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
