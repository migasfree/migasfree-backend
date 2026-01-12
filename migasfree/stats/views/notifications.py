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

from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, OpenApiTypes, extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...client.models import Notification
from .events import event_by_month, month_interval


@extend_schema(tags=['stats'])
@permission_classes((permissions.IsAuthenticated,))
class NotificationStatsViewSet(viewsets.ViewSet):
    serializer_class = None

    @extend_schema(
        description=(
            'Returns notification statistics grouped by month for the interval '
            'defined by the optional *begin* and *end* query parameters.'
        ),
        parameters=[
            OpenApiParameter(
                name='begin',
                description='Start month in YYYY-MM format (optional)',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name='end',
                description='End month in YYYY-MM format (optional)',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Notification counts grouped by month and by “checked” status.',
                examples=[
                    OpenApiExample(
                        'successfully response',
                        value={
                            'x_labels': ['2025-06', '2025-07', '2025-08', '2025-09'],
                            'data': {
                                'Checked': [
                                    {'value': 0},
                                    {
                                        'value': 3,
                                        'model': 'notification',
                                        'checked__exact': 1,
                                        'created_at__gte': '2025-07-01',
                                        'created_at__lt': '2025-08-01',
                                    },
                                    {
                                        'value': 4,
                                        'model': 'notification',
                                        'checked__exact': 1,
                                        'created_at__gte': '2025-08-01',
                                        'created_at__lt': '2025-09-01',
                                    },
                                    {'value': 0},
                                ],
                                'Unchecked': [
                                    {'value': 0},
                                    {
                                        'value': 0,
                                        'model': 'notification',
                                        'checked__exact': 0,
                                        'created_at__gte': '2025-07-01',
                                        'created_at__lt': '2025-08-01',
                                    },
                                    {
                                        'value': 0,
                                        'model': 'notification',
                                        'checked__exact': 0,
                                        'created_at__gte': '2025-08-01',
                                        'created_at__lt': '2025-09-01',
                                    },
                                    {'value': 0},
                                ],
                            },
                        },
                    )
                ],
            )
        },
    )
    @action(methods=['get'], detail=False, url_path='month')
    def by_month(self, request):
        begin_date, end_date = month_interval(
            begin_month=request.query_params.get('begin', ''), end_month=request.query_params.get('end', '')
        )

        data = event_by_month(
            Notification.stacked_by_month(begin_date), begin_date, end_date, 'notification', field='checked'
        )
        return Response(data, status=status.HTTP_200_OK)
