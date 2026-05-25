# Copyright (c) 2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2026 Alberto Gacías <alberto@migasfree.org>
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

import logging

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ..client.models import Computer
from ..core.mixins import SafeConnectionMixin
from . import models, serializers

logger = logging.getLogger('migasfree')


@extend_schema(tags=['safe'])
@permission_classes((permissions.AllowAny,))
class SafeDeviceViewSet(SafeConnectionMixin, viewsets.ViewSet):
    @extend_schema(
        description='Returns available physical devices for a given computer (requires mTLS)',
        responses={
            status.HTTP_200_OK: serializers.DeviceSerializer(many=True),
            status.HTTP_400_BAD_REQUEST: {'description': 'Error in request'},
        },
    )
    @action(methods=['post'], detail=False)
    def available(self, request):
        claims = self.get_claims(request.data)
        if isinstance(claims, str):
            return Response(self.create_response(claims), status=status.HTTP_400_BAD_REQUEST)

        if not claims or 'cid' not in claims:
            return Response(self.create_response(_('Malformed claims')), status=status.HTTP_400_BAD_REQUEST)

        computer = get_object_or_404(Computer, pk=claims.get('cid'))
        query = claims.get('q', '')

        # Filter by computer project to mimic UserProfile scoping in safe mode
        results = models.Device.objects.available_for_computer(computer, query, None)
        # Filter strictly to the computer project as the client does not have a user profile
        results = results.filter(project=computer.project)

        serializer = serializers.DeviceSerializer(results, many=True)
        return Response(self.create_response(serializer.data), status=status.HTTP_200_OK)


@extend_schema(tags=['safe'])
@permission_classes((permissions.AllowAny,))
class SafeLogicalViewSet(SafeConnectionMixin, viewsets.ViewSet):
    @extend_schema(
        description='Returns available logical devices for a given computer (requires mTLS)',
        responses={
            status.HTTP_200_OK: serializers.LogicalSerializer(many=True),
            status.HTTP_400_BAD_REQUEST: {'description': 'Error in request'},
        },
    )
    @action(methods=['post'], detail=False)
    def available(self, request):
        claims = self.get_claims(request.data)
        if isinstance(claims, str):
            return Response(self.create_response(claims), status=status.HTTP_400_BAD_REQUEST)

        if not claims or 'cid' not in claims:
            return Response(self.create_response(_('Malformed claims')), status=status.HTTP_400_BAD_REQUEST)

        computer = get_object_or_404(Computer, pk=claims.get('cid'))
        query = claims.get('q', '')
        device = claims.get('did', 0)

        results = (
            models.Logical.objects.select_related('device', 'device__model', 'capability')
            .prefetch_related('device__available_for_attributes')
            .filter(device__available_for_attributes__in=computer.sync_attributes.values_list('id', flat=True))
            .filter(project=computer.project)
            .order_by('device__name', 'capability__name')
            .distinct()
        )
        if query:
            results = results.filter(Q(device__name__icontains=query) | Q(device__data__icontains=query))
        if device:
            results = results.filter(device__id=device)

        serializer = serializers.LogicalSerializer(results, many=True)
        return Response(self.create_response(serializer.data), status=status.HTTP_200_OK)


@extend_schema(tags=['safe'])
@permission_classes((permissions.AllowAny,))
class SafeCapabilityViewSet(SafeConnectionMixin, viewsets.ViewSet):
    @extend_schema(
        description='Returns capabilities for a given capability ID (requires mTLS)',
        responses={
            status.HTTP_200_OK: serializers.CapabilitySerializer(many=True),
            status.HTTP_400_BAD_REQUEST: {'description': 'Error in request'},
        },
    )
    def create(self, request):
        claims = self.get_claims(request.data)
        if isinstance(claims, str):
            return Response(self.create_response(claims), status=status.HTTP_400_BAD_REQUEST)

        cid = claims.get('id') if isinstance(claims, dict) else None

        results = models.Capability.objects.all().order_by('name')
        if cid:
            results = results.filter(id=cid)

        serializer = serializers.CapabilitySerializer(results, many=True)
        return Response(self.create_response(serializer.data), status=status.HTTP_200_OK)
