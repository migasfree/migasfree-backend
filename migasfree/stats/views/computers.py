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

from django.db.models.aggregates import Count
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, OpenApiTypes, extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...client.models import Computer
from ...utils import replace_keys
from .events import event_by_month, month_interval


@extend_schema(tags=['stats'])
@permission_classes((permissions.IsAuthenticated,))
class ComputerStatsViewSet(viewsets.ViewSet):
    serializer_class = None

    @extend_schema(
        description='Returns the number of computers grouped by project for the requesting user.',
        responses=OpenApiResponse(
            description='Response containing a list of projects with their IDs, names and counts, plus a total.',
            response={
                'type': 'object',
                'properties': {
                    'data': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string'},
                                'project_id': {'type': 'integer'},
                                'value': {'type': 'integer'},
                            },
                            'required': ['name', 'project_id', 'value'],
                        },
                    },
                    'total': {'type': 'integer'},
                },
                'required': ['data', 'total'],
            },
            examples=[
                OpenApiExample(
                    'successfully response',
                    value={
                        'data': [
                            {'name': 'Project Alpha', 'project_id': 1, 'value': 42},
                            {'name': 'Project Beta', 'project_id': 2, 'value': 17},
                        ],
                        'total': 69,
                    },
                    response_only=True,
                    status_codes=[status.HTTP_200_OK],
                )
            ],
        ),
    )
    @action(methods=['get'], detail=False)
    def projects(self, request):
        data = Computer.group_by_project(request.user.userprofile)
        response = {
            'data': replace_keys(list(data), {'project__name': 'name', 'project__id': 'project_id', 'count': 'value'}),
            'total': data.count(),
        }

        return Response(response, status=status.HTTP_200_OK)

    @extend_schema(
        description='Returns the number of computers grouped by platform for the requesting user.',
        responses=OpenApiResponse(
            description='Response containing a list of platforms with their IDs, names and counts, plus a total.',
            response={
                'type': 'object',
                'properties': {
                    'data': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string'},
                                'platform_id': {'type': 'integer'},
                                'value': {'type': 'integer'},
                            },
                            'required': ['name', 'platform_id', 'value'],
                        },
                    },
                    'total': {'type': 'integer'},
                },
                'required': ['data', 'total'],
            },
            examples=[
                OpenApiExample(
                    'successfully response',
                    value={
                        'data': [
                            {'name': 'Linux', 'platform_id': 1, 'value': 120},
                            {'name': 'Windows', 'platform_id': 2, 'value': 85},
                            {'name': 'macOS', 'platform_id': 3, 'value': 30},
                        ],
                        'total': 235,
                    },
                    response_only=True,
                    status_codes=[status.HTTP_200_OK],
                )
            ],
        ),
    )
    @action(methods=['get'], detail=False)
    def platforms(self, request):
        data = Computer.group_by_platform(request.user.userprofile)
        response = {
            'data': replace_keys(
                list(data),
                {'project__platform__name': 'name', 'project__platform__id': 'platform_id', 'count': 'value'},
            ),
            'total': data.count(),
        }

        return Response(response, status=status.HTTP_200_OK)

    @extend_schema(
        description='Returns the total number of computers grouped by machine type '
        '(virtual/physical) and subscription status.',
        responses=OpenApiResponse(
            description='Response with title, total count and two arrays (inner & outer) describing the groups.',
            response={
                'type': 'object',
                'properties': {
                    'title': {'type': 'string'},
                    'total': {'type': 'integer'},
                    'inner': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string'},
                                'value': {'type': 'integer'},
                                'status_in': {'type': 'string'},
                            },
                            'required': ['name', 'value', 'status_in'],
                        },
                    },
                    'outer': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string'},
                                'value': {'type': 'integer'},
                                'status_in': {'type': 'string'},
                                'machine': {'type': 'string'},
                            },
                            'required': ['name', 'value', 'status_in', 'machine'],
                        },
                    },
                },
                'required': ['title', 'total', 'inner', 'outer'],
            },
            examples=[
                OpenApiExample(
                    'Response example',
                    value={
                        'title': 'Computers / Machine',
                        'total': 250,
                        'inner': [
                            {
                                'name': 'Subscribed',
                                'value': 180,
                                'status_in': Computer.SUBSCRIBED_STATUS_CSV,
                            },
                            {'name': 'Unsubscribed', 'value': 70, 'status_in': 'unsubscribed'},
                        ],
                        'outer': [
                            {
                                'name': 'Virtual',
                                'value': 100,
                                'status_in': Computer.SUBSCRIBED_STATUS_CSV,
                                'machine': 'V',
                            },
                            {
                                'name': 'Physical',
                                'value': 80,
                                'status_in': Computer.SUBSCRIBED_STATUS_CSV,
                                'machine': 'P',
                            },
                            {'name': 'Virtual', 'value': 20, 'status_in': 'unsubscribed', 'machine': 'V'},
                            {'name': 'Physical', 'value': 50, 'status_in': 'unsubscribed', 'machine': 'P'},
                        ],
                    },
                    response_only=True,
                    status_codes=[status.HTTP_200_OK],
                )
            ],
        ),
    )
    @action(methods=['get'], detail=False, url_path='machine')
    def by_machine(self, request):
        from django.db.models import Case, IntegerField, Q, When

        user_scope = Computer.objects.scope(request.user.userprofile)

        # Single aggregated query instead of 6 separate queries
        counts = user_scope.aggregate(
            total=Count('id'),
            subscribed=Count(Case(When(~Q(status='unsubscribed'), then=1), output_field=IntegerField())),
            subscribed_virtual=Count(
                Case(When(~Q(status='unsubscribed'), machine='V', then=1), output_field=IntegerField())
            ),
            subscribed_physical=Count(
                Case(When(~Q(status='unsubscribed'), machine='P', then=1), output_field=IntegerField())
            ),
            unsubscribed=Count(Case(When(status='unsubscribed', then=1), output_field=IntegerField())),
            unsubscribed_virtual=Count(
                Case(When(status='unsubscribed', machine='V', then=1), output_field=IntegerField())
            ),
            unsubscribed_physical=Count(
                Case(When(status='unsubscribed', machine='P', then=1), output_field=IntegerField())
            ),
        )

        data = {
            'inner': [],
            'outer': [],
        }

        if counts['subscribed']:
            if counts['subscribed_virtual']:
                data['outer'].append(
                    {
                        'name': _('Virtual'),
                        'value': counts['subscribed_virtual'],
                        'status_in': Computer.SUBSCRIBED_STATUS_CSV,
                        'machine': 'V',
                    }
                )

            if counts['subscribed_physical']:
                data['outer'].append(
                    {
                        'name': _('Physical'),
                        'value': counts['subscribed_physical'],
                        'status_in': Computer.SUBSCRIBED_STATUS_CSV,
                        'machine': 'P',
                    }
                )

            data['inner'].append(
                {
                    'name': _('Subscribed'),
                    'value': counts['subscribed'],
                    'status_in': Computer.SUBSCRIBED_STATUS_CSV,
                },
            )

        if counts['unsubscribed']:
            if counts['unsubscribed_virtual']:
                data['outer'].append(
                    {
                        'name': _('Virtual'),
                        'value': counts['unsubscribed_virtual'],
                        'status_in': 'unsubscribed',
                        'machine': 'V',
                    }
                )

            if counts['unsubscribed_physical']:
                data['outer'].append(
                    {
                        'name': _('Physical'),
                        'value': counts['unsubscribed_physical'],
                        'status_in': 'unsubscribed',
                        'machine': 'P',
                    }
                )

            data['inner'].append(
                {'name': _('Unsubscribed'), 'value': counts['unsubscribed'], 'status_in': 'unsubscribed'}
            )

        return Response(
            {
                'title': _('Computers / Machine'),
                'total': counts['total'],
                'inner': data['inner'],
                'outer': data['outer'],
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        description='Returns the total number of subscribed computers grouped by status and by productivity '
        '(productive / unproductive).',
        responses=OpenApiResponse(
            description='Response containing title, total count and two arrays (inner & outer) describing the groups.',
            response={
                'type': 'object',
                'properties': {
                    'title': {'type': 'string'},
                    'total': {'type': 'integer'},
                    'inner': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string'},
                                'value': {'type': 'integer'},
                                'status_in': {'type': 'string'},
                            },
                            'required': ['name', 'value', 'status_in'],
                        },
                    },
                    'outer': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string'},
                                'value': {'type': 'integer'},
                                'status_in': {'type': 'string'},
                            },
                            'required': ['name', 'value', 'status_in'],
                        },
                    },
                },
                'required': ['title', 'total', 'inner', 'outer'],
            },
            examples=[
                OpenApiExample(
                    'successfully response',
                    value={
                        'title': 'Subscribed Computers / Status',
                        'total': 300,
                        'inner': [
                            {'name': 'Productive', 'value': 210, 'status_in': Computer.PRODUCTIVE_STATUS_CSV},
                            {'name': 'Unproductive', 'value': 90, 'status_in': 'in repair,available'},
                        ],
                        'outer': [
                            {'name': 'Intended', 'value': 120, 'status_in': 'intended'},
                            {'name': 'Reserved', 'value': 60, 'status_in': 'reserved'},
                            {'name': 'Unknown', 'value': 30, 'status_in': 'unknown'},
                            {'name': 'Available', 'value': 70, 'status_in': 'available'},
                            {'name': 'In repair', 'value': 20, 'status_in': 'in repair'},
                        ],
                    },
                    response_only=True,
                    status_codes=[status.HTTP_200_OK],
                )
            ],
        ),
    )
    @action(methods=['get'], detail=False, url_path='status')
    def by_status(self, request):
        total = Computer.objects.scope(request.user.userprofile).exclude(status='unsubscribed').count()

        data = {
            'inner': [],
            'outer': [],
        }

        values = {}
        for item in (
            Computer.objects.scope(request.user.userprofile)
            .exclude(status='unsubscribed')
            .values('status')
            .annotate(count=Count('id'))
            .order_by('status', '-count')
        ):
            status_name = _(dict(Computer.STATUS_CHOICES)[item.get('status')])
            values[item.get('status')] = {
                'name': status_name,
                'value': item.get('count'),
                'status_in': item.get('status'),
            }

        count_productive = (
            values.get('intended', {}).get('value', 0)
            + values.get('reserved', {}).get('value', 0)
            + values.get('unknown', {}).get('value', 0)
        )
        if 'intended' in values:
            data['outer'].append(values['intended'])
        if 'reserved' in values:
            data['outer'].append(values['reserved'])
        if 'unknown' in values:
            data['outer'].append(values['unknown'])

        count_unproductive = values.get('available', {}).get('value', 0) + values.get('in repair', {}).get('value', 0)
        if 'available' in values:
            data['outer'].append(values['available'])
        if 'in repair' in values:
            data['outer'].append(values['in repair'])

        data['inner'] = [
            {
                'name': _('Productive'),
                'value': count_productive,
                'status_in': Computer.PRODUCTIVE_STATUS_CSV,
            },
            {
                'name': _('Unproductive'),
                'value': count_unproductive,
                'status_in': 'in repair,available',
            },
        ]

        return Response(
            {
                'title': _('Subscribed Computers / Status'),
                'total': total,
                'inner': data['inner'],
                'outer': data['outer'],
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        description='Returns the number of computers that match the specified attributes.',
        parameters=[
            OpenApiParameter(
                name='attributes',
                description='List of attributes to count (can be repeated)',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                many=True,
            ),
            OpenApiParameter(
                name='project_id',
                description='Proyect ID (optional)',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={status.HTTP_200_OK: OpenApiTypes.INT},
    )
    @action(methods=['get'], detail=False, url_path='attributes/count')
    def attributes_count(self, request):
        attributes = request.query_params.getlist('attributes')
        project_id = request.query_params.get('project_id', None)

        return Response(Computer.count_by_attributes(attributes, project_id), status=status.HTTP_200_OK)

    @extend_schema(
        description='Returns the number of new computers created per month within the given interval.',
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
        responses={status.HTTP_200_OK: OpenApiTypes.OBJECT},
    )
    @action(methods=['get'], detail=False, url_path='new/month')
    def new_by_month(self, request):
        begin_date, end_date = month_interval(
            begin_month=request.query_params.get('begin', ''), end_month=request.query_params.get('end', '')
        )

        data = event_by_month(
            Computer.stacked_by_month(request.user.userprofile, begin_date), begin_date, end_date, Computer
        )
        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        description=(
            'Returns productive computers grouped by platform (inner) and by '
            'project + platform (outer). Keys are renamed for a cleaner API output.'
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description=(
                    'Dictionary with the total number of productive computers and '
                    'breakdowns by platform (inner) and by project/platform (outer).'
                ),
                examples=[
                    OpenApiExample(
                        'successfully response',
                        value={
                            'total': 123,
                            'inner': [
                                {'platform_id': 1, 'name': 'Linux', 'value': 80},
                                {'platform_id': 2, 'name': 'Windows', 'value': 43},
                            ],
                            'outer': [
                                {'name': 'Project A', 'project_id': 10, 'platform_id': 1, 'value': 50},
                                {'name': 'Project B', 'project_id': 11, 'platform_id': 1, 'value': 30},
                                {'name': 'Project C', 'project_id': 11, 'platform_id': 2, 'value': 43},
                            ],
                        },
                    )
                ],
            )
        },
    )
    @action(methods=['get'], detail=False, url_path='productive/platform')
    def productive_by_platform(self, request):
        data = Computer.productive_computers_by_platform(request.user.userprofile)
        inner_aliases = {'project__platform__id': 'platform_id', 'project__platform__name': 'name', 'count': 'value'}
        outer_aliases = {
            'project__name': 'name',
            'project__id': 'project_id',
            'project__platform__id': 'platform_id',
            'count': 'value',
        }

        return Response(
            {
                'total': data['total'],
                'inner': replace_keys(data['inner'], inner_aliases),
                'outer': replace_keys(data['outer'], outer_aliases),
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        description=(
            'Returns the number of computers entered each year for the current '
            'user profile, together with helper fields useful for frontend '
            'filtering.'
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description=(
                    'Statistics of computer entries per year. Returns a list of '
                    'labels (years) and a data dict where each entry contains the '
                    'count for that year plus auxiliary filter information.'
                ),
                examples=[
                    OpenApiExample(
                        'successfully response',
                        value={
                            'x_labels': [2022, 2023, 2024],
                            'data': {
                                'Computers': [
                                    {
                                        'value': 150,
                                        'machine': 'P',
                                        'created_at__gte': '2022-01-01',
                                        'created_at__lt': '2023-01-01',
                                    },
                                    {
                                        'value': 180,
                                        'machine': 'P',
                                        'created_at__gte': '2023-01-01',
                                        'created_at__lt': '2024-01-01',
                                    },
                                    {
                                        'value': 200,
                                        'machine': 'P',
                                        'created_at__gte': '2024-01-01',
                                        'created_at__lt': '2025-01-01',
                                    },
                                ]
                            },
                        },
                    )
                ],
            )
        },
    )
    @action(methods=['get'], detail=False, url_path='entry/year')
    def entry_year(self, request):
        results = Computer.entry_year(request.user.userprofile)
        data = [x['count'] for x in results]
        labels = [x['year'] for x in results]

        for i, _item in enumerate(labels):
            data[i] = {
                'value': data[i],
                'machine': 'P',
                'created_at__gte': f'{labels[i]}-01-01',
                'created_at__lt': f'{labels[i] + 1}-01-01',
            }

        return Response({'x_labels': labels, 'data': {_('Computers'): data}}, status=status.HTTP_200_OK)
