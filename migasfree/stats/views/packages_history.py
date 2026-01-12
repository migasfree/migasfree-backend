# Copyright (c) 2021-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2021-2026 Alberto Gacías <alberto@migasfree.org>
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

from django.db.models import Count
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, OpenApiTypes, extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...client.models import PackageHistory


@extend_schema(tags=['stats'])
@permission_classes((permissions.IsAuthenticated,))
class PackageHistoryStatsViewSet(viewsets.ViewSet):
    serializer_class = None

    @extend_schema(
        description=(
            'Returns the amount of packages per project for the authenticated '
            'user profile. The response contains a title, the overall total, '
            'and a list of objects with the project name, the package count '
            "(value), and the project's internal ID."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description=(
                    'Number of packages grouped by project for the current user '
                    'profile. Includes a total count and a list of project-wise '
                    'aggregations.'
                ),
                examples=[
                    OpenApiExample(
                        'successfully response',
                        value={
                            'title': 'Packages / Project',
                            'total': 123,
                            'data': [
                                {'name': 'Project Alpha', 'value': 78, 'package_project_id': 10},
                                {'name': 'Project Beta', 'value': 45, 'package_project_id': 12},
                            ],
                        },
                    )
                ],
            )
        },
    )
    @action(methods=['get'], detail=False, url_path='project')
    def by_project(self, request):
        total = PackageHistory.objects.scope(request.user.userprofile).count()

        data = [
            {
                'name': item.get('package__project__name'),
                'value': item.get('count'),
                'package_project_id': item.get('package__project__id'),
            }
            for item in PackageHistory.objects.scope(request.user.userprofile)
            .values('package__project__id', 'package__project__name')
            .annotate(count=Count('package__project__id'))
            .order_by('-count')
        ]

        return Response(
            {
                'title': _('Packages / Project'),
                'total': total,
                'data': data,
            },
            status=status.HTTP_200_OK,
        )
