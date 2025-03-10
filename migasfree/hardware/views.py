# -*- coding: utf-8 *-*

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

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes, OpenApiResponse
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status, mixins, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ..core.mixins import SafeConnectionMixin
from ..core.views import MigasViewSet
from ..client.models import Computer
from ..client.serializers import ComputerInfoSerializer
from ..mixins import DatabaseCheckMixin

from .models import Node, Capability, LogicalName, Configuration
from .filters import NodeFilter
from . import tasks, serializers


@permission_classes((permissions.DjangoModelPermissions,))
class HardwareViewSet(
    DatabaseCheckMixin,
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    viewsets.GenericViewSet, MigasViewSet
):
    queryset = Node.objects.all()
    serializer_class = serializers.NodeSerializer
    filterset_class = NodeFilter
    ordering_fields = '__all__'
    ordering = ('id',)

    # example cpu list: bus_info='cpu@' or bus_info='cpu@0'

    def get_queryset(self):
        if self.request is None:
            return Node.objects.none()

        return Node.objects.scope(self.request.user.userprofile)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Identifier of the node',
                required=True,
            )
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(description='Successfully retrieved node information'),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description='Authentication credentials were not provided'),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(description='Permission denied for this operation'),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(description='Node not found'),
        },
        summary='Retrieve detailed information about a specific node',
        description='This endpoint provides comprehensive details about a node, including its capabilities, '
        'logical names, and configurations.',
    )
    @action(methods=['get'], detail=True)
    def info(self, request, pk=None):
        node = self.get_object()
        request.user.userprofile.check_scope(node.computer.id)

        capability = Capability.objects.filter(node=node.id).values(
            'name', 'description'
        )
        logical_name = LogicalName.objects.filter(node=node.id).values('name')
        configuration = Configuration.objects.filter(node=node.id).values(
            'name', 'value'
        )

        name = node.__str__()
        if not name:
            name = node.description
            if node.product:
                name = f'{name}: {node.product}'

        data = {
            'name': name,
            'computer': ComputerInfoSerializer(node.computer).data,
            'capability': serializers.CapabilityInfoSerializer(
                capability, many=True
            ).data,
            'logical_name': serializers.LogicalNameInfoSerializer(
                logical_name, many=True
            ).data,
            'configuration': serializers.ConfigurationInfoSerializer(
                configuration, many=True
            ).data,
        }

        return Response(
            data,
            status=status.HTTP_200_OK
        )


@permission_classes((permissions.AllowAny,))
class SafeHardwareViewSet(SafeConnectionMixin, viewsets.ViewSet):
    @action(methods=['post'], detail=False)
    def hardware(self, request):
        """
        claims = {
            'id': computer_id,
            'hardware': json_structure,
        }
        """

        claims = self.get_claims(request.data)
        if not claims or 'id' not in claims or 'hardware' not in claims:
            return Response(
                self.create_response(gettext('Malformed claims')),
                status=status.HTTP_400_BAD_REQUEST
            )

        computer = get_object_or_404(Computer, id=claims.get('id'))

        hw_data = claims.get('hardware')
        if isinstance(hw_data, list):
            hw_data = hw_data[0]

        Node.objects.filter(computer=computer).delete()
        tasks.save_computer_hardware.delay(computer.id, hw_data)
        computer.update_last_hardware_capture()
        computer.update_hardware_resume()

        return Response(
            self.create_response(gettext('Data received')),
            status=status.HTTP_200_OK
        )
