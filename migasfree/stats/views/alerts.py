# Copyright (c) 2020-2025 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2020-2025 Alberto Gacías <alberto@migasfree.org>
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

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import permission_classes
from rest_framework.response import Response

from ...mixins import DatabaseCheckMixin
from ..tasks import get_alerts


@extend_schema(tags=['stats'])
@permission_classes((permissions.IsAuthenticated,))
class AlertsViewSet(DatabaseCheckMixin, viewsets.ViewSet):
    serializer_class = None

    @extend_schema(
        summary='Retrieves the list of alerts',
        description=('Returns all current alerts for the authenticated user. The response is a JSON arrays list.'),
        responses={
            status.HTTP_200_OK: {'description': 'Successful retrieval of alerts'},
        },
        examples=[
            OpenApiExample(
                name='successfully response',
                value={
                    'result': '3',
                    'api': {
                        'model': 'packages',
                        'query': {
                            'deployment': True,
                            'store': False,
                            'packageset': True,
                        },
                    },
                    'level': 'warning',
                    'target': 'server',
                    'msg': 'Orphan packages',
                },
                response_only=True,
            )
        ],
    )
    def list(self, request):
        return Response(get_alerts(), status=status.HTTP_200_OK)
