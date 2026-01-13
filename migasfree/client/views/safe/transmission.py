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
Safe transmission views (EOT and Synchronization).
"""

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiExample, OpenApiTypes, extend_schema, inline_serializer
from rest_framework import permissions, status, views
from rest_framework import serializers as drf_serializers
from rest_framework.decorators import permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from ....core.mixins import SafeConnectionMixin
from ... import models, serializers
from ...messages import add_computer_message, remove_computer_messages


@extend_schema(tags=['safe'])
@permission_classes((permissions.AllowAny,))
@throttle_classes([UserRateThrottle])
class SafeEndOfTransmissionView(SafeConnectionMixin, views.APIView):
    @extend_schema(
        description='Returns 200 if ok, 404 if computer not found (requires JWT auth)',
        request={'id': OpenApiTypes.INT},
        responses={
            status.HTTP_200_OK: {'description': gettext('EOT OK')},
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
        examples=[
            OpenApiExample(
                name='successfully response',
                value=gettext('EOT OK'),
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        """
        claims = {"id": id}
        """
        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        remove_computer_messages(computer.id)

        if computer.status == 'available':
            models.Notification.objects.create(
                _('Computer [%s] with available status, has been synchronized') % computer
            )

        return Response(self.create_response(gettext('EOT OK')), status=status.HTTP_200_OK)


@extend_schema(tags=['safe'])
@permission_classes((permissions.AllowAny,))
@throttle_classes([UserRateThrottle])
class SafeSynchronizationView(SafeConnectionMixin, views.APIView):
    @extend_schema(
        description='Creates a computer synchronization (requires JWT auth)',
        request=inline_serializer(
            name='SafeSyncRequest',
            fields={
                'id': drf_serializers.IntegerField(),
                'start_date': drf_serializers.DateTimeField(),
                'consumer': drf_serializers.CharField(),
                'pms_status_ok': drf_serializers.BooleanField(),
            },
        ),
        responses={
            status.HTTP_201_CREATED: serializers.SynchronizationWriteSerializer,
            status.HTTP_400_BAD_REQUEST: {'description': 'Error in request'},
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
    )
    def post(self, request):
        """
        claims = {
            "id": id,
            "start_date": datetime,
            "consumer": string,
            "pms_status_ok": true|false
        }
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))
        self.verify_mtls_identity(request, computer.uuid)

        add_computer_message(computer, gettext('Getting synchronization...'))

        data = {
            'computer': computer.id,
            'user': computer.sync_user.id,
            'project': self.project.id,
            'start_date': claims.get('start_date'),
            'consumer': claims.get('consumer'),
            'pms_status_ok': claims.get('pms_status_ok', False),
        }
        serializer = serializers.SynchronizationWriteSerializer(data=data)

        add_computer_message(computer, gettext('Sending synchronization...'))

        if serializer.is_valid():
            serializer.save()

            return Response(self.create_response(serializer.data), status=status.HTTP_201_CREATED)

        return Response(self.create_response(serializer.errors), status=status.HTTP_400_BAD_REQUEST)
