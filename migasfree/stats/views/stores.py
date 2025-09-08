# -*- coding: UTF-8 -*-

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

from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema, OpenApiTypes, OpenApiResponse, OpenApiExample
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...core.models import Store
from ...utils import replace_keys


@extend_schema(tags=['stats'])
@permission_classes((permissions.IsAuthenticated,))
class StoreStatsViewSet(viewsets.ViewSet):
    serializer_class = None

    @extend_schema(
        description=(
            "Returns the number of stores per project for the current user's "
            "profile. Keys are renamed (`project__name` → `name`, "
            "`project__id` → `project_id`, `count` → `value`) for a cleaner API."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description=(
                    "Stores grouped by project for the authenticated user profile. "
                    "The payload contains a title, the total number of stores, "
                    "and a list of projects with the amount of stores per project."
                ),
                examples=[
                    OpenApiExample(
                        "successfully response",
                        value={
                            "title": "Stores / Project",
                            "total": 42,
                            "data": [
                                {
                                    "name": "Project Alpha",
                                    "project_id": 10,
                                    "value": 18
                                },
                                {
                                    "name": "Project Beta",
                                    "project_id": 12,
                                    "value": 24
                                }
                            ]
                        }
                    )
                ],
            )
        },
    )
    @action(methods=['get'], detail=False, url_path='project')
    def by_project(self, request):
        user = request.user.userprofile

        return Response(
            {
                'title': _('Stores / Project'),
                'total': Store.objects.scope(user).count(),
                'data': replace_keys(
                    list(Store.group_by_project(user)),
                    {
                        'project__name': 'name',
                        'project__id': 'project_id',
                        'count': 'value'
                    }
                ),
            },
            status=status.HTTP_200_OK
        )
