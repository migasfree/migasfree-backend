# -*- coding: utf-8 *-*

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

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext
from rest_framework import viewsets, status, mixins, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ..core.mixins import SafeConnectionMixin
from ..core.views import MigasViewSet
from ..client.models import Computer

from .models import Node
from .filters import NodeFilter
from . import tasks, serializers


@permission_classes((permissions.DjangoModelPermissions,))
class HardwareComputerViewSet(viewsets.ViewSet):
    queryset = Node.objects.all()  # FIXME

    @action(methods=['get'], detail=True)
    def hardware(self, request, pk=None):
        computer = get_object_or_404(Computer, pk=pk)
        nodes = Node.objects.filter(computer=computer).order_by('id')

        serializer = serializers.NodeSerializer(nodes, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


@permission_classes((permissions.DjangoModelPermissions,))
class HardwareViewSet(
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

        user = self.request.user.userprofile
        qs = self.queryset
        if not user.is_view_all():
            qs = qs.filter(computer_id__in=user.get_computers())

        return qs


@permission_classes((permissions.AllowAny,))
class SafeHardwareViewSet(SafeConnectionMixin, viewsets.ViewSet):
    @action(methods=['post'], detail=False)
    def hardware(self, request, format=None):
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
