# -*- coding: utf-8 *-*

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

from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from rest_framework import viewsets, status, filters, mixins
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework_filters import backends

from migasfree.core.mixins import SafeConnectionMixin
from migasfree.client.models import Computer
from migasfree.utils import trans

from .models import Node
from .filters import NodeFilter
from . import tasks, serializers


class HardwareComputerViewSet(viewsets.ViewSet):
    @detail_route(methods=['get'])
    def hardware(self, request, pk=None):
        computer = get_object_or_404(Computer, pk=pk)
        nodes = Node.objects.filter(computer=computer).order_by('id')

        serializer = serializers.NodeSerializer(nodes, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class HardwareViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Node.objects.all()
    serializer_class = serializers.NodeSerializer
    filter_class = NodeFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)
    ordering_fields = '__all__'
    ordering = ('id',)
    paginate_by = 100  # FIXME constant

    # example cpu list: bus_info='cpu@' or bus_info='cpu@0'


class SafeHardwareViewSet(SafeConnectionMixin, viewsets.ViewSet):
    @list_route(methods=['post'])
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
                self.create_response(trans('Malformed claims')),
                status=status.HTTP_400_BAD_REQUEST
            )

        computer = get_object_or_404(Computer, id=claims.get('id'))

        Node.objects.filter(computer=computer).delete()
        tasks.save_computer_hardware.delay(computer.id, claims.get('hardware'))
        computer.update_last_hardware_capture()

        return Response(
            self.create_response(trans('Data received')),
            status=status.HTTP_200_OK
        )
