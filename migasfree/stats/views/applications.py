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
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...app_catalog.models import Application


@extend_schema(tags=['stats'])
@permission_classes((permissions.IsAuthenticated,))
class ApplicationStatsViewSet(viewsets.ViewSet):
    serializer_class = None

    @extend_schema(
        description='Returns the total number of applications grouped by category.',
        responses=OpenApiResponse(
            description='Response containing a title, total count, and a list of categories.',
            response={
                'type': 'object',
                'properties': {
                    'title': {'type': 'string'},
                    'total': {'type': 'integer'},
                    'data': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string'},
                                'value': {'type': 'integer'},
                                'category': {'type': 'integer'},
                            },
                        },
                    },
                },
                'required': ['title', 'total', 'data'],
            },
            examples=[
                OpenApiExample(
                    'successfully response',
                    value={
                        'title': 'Applications / Category',
                        'total': 15,
                        'data': [
                            {'name': 'Category A', 'value': 10, 'category': 1},
                            {'name': 'Category B', 'value': 5, 'category': 2},
                        ],
                    },
                    response_only=True,
                    status_codes=[status.HTTP_200_OK],
                )
            ],
        ),
    )
    @action(methods=['get'], detail=False, url_path='category')
    def by_category(self, request):
        total = Application.objects.count()

        data = [
            {'name': item.get('category__name'), 'value': item.get('count'), 'category': item.get('category__id')}
            for item in Application.group_by_category()
        ]

        return Response(
            {
                'title': _('Applications / Category'),
                'total': total,
                'data': data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        description='Returns the total number of applications grouped by level.',
        responses=OpenApiResponse(
            description='Response containing a title, total count, and a list of levels.',
            response={
                'type': 'object',
                'properties': {
                    'title': {'type': 'string'},
                    'total': {'type': 'integer'},
                    'data': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string'},
                                'value': {'type': 'integer'},
                                'level': {'type': 'integer'},
                            },
                        },
                    },
                },
                'required': ['title', 'total', 'data'],
            },
            examples=[
                OpenApiExample(
                    'Response example',
                    value={
                        'title': 'Applications / Level',
                        'total': 17,
                        'data': [
                            {'name': 'User', 'value': 5, 'level': 1},
                            {'name': 'Admin', 'value': 12, 'level': 2},
                        ],
                    },
                    response_only=True,
                    status_codes=[status.HTTP_200_OK],
                )
            ],
        ),
    )
    @action(methods=['get'], detail=False, url_path='level')
    def by_level(self, request):
        total = Application.objects.count()

        data = [
            {
                'name': dict(Application.LEVELS)[item.get('level')],
                'value': item.get('count'),
                'level': item.get('level'),
            }
            for item in Application.group_by_level()
        ]

        return Response(
            {
                'title': _('Applications / Level'),
                'total': total,
                'data': data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        description='Returns the total number of applications grouped by project.',
        responses=OpenApiResponse(
            description='Response containing x-axis labels, data points and total count.',
            response={
                'type': 'object',
                'properties': {
                    'x_labels': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'Project names (x-axis labels).',
                    },
                    'data': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'value': {'type': 'integer'},
                                'packages_by_project__project__id': {'type': 'integer'},
                            },
                            'required': ['value', 'packages_by_project__project__id'],
                        },
                    },
                    'total': {'type': 'integer'},
                },
                'required': ['x_labels', 'data', 'total'],
            },
            examples=[
                OpenApiExample(
                    'successfully response',
                    value={
                        'x_labels': ['Project A', 'Project B', 'Project C'],
                        'data': [
                            {'value': 12, 'packages_by_project__project__id': 1},
                            {'value': 7, 'packages_by_project__project__id': 2},
                            {'value': 3, 'packages_by_project__project__id': 3},
                        ],
                        'total': 22,
                    },
                    response_only=True,
                    status_codes=[status.HTTP_200_OK],
                )
            ],
        ),
    )
    @action(methods=['get'], detail=False, url_path='project')
    def by_project(self, request):
        total = Application.objects.count()

        x_axe = []
        data = []
        for item in Application.group_by_project():
            x_axe.append(item['packages_by_project__project__name'])
            data.append(
                {'value': item['count'], 'packages_by_project__project__id': item['packages_by_project__project__id']}
            )

        return Response({'x_labels': x_axe, 'data': data, 'total': total}, status=status.HTTP_200_OK)
