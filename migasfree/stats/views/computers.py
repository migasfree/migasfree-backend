# -*- coding: UTF-8 -*-

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

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...client.models import Computer
from ...utils import replace_keys

from .events import event_by_month, month_interval


@permission_classes((permissions.IsAuthenticated,))
class ComputerStatsViewSet(viewsets.ViewSet):
    @action(methods=['get'], detail=False)
    def projects(self, request, format=None):
        return Response(
            replace_keys(
                list(Computer.group_by_project()),
                {
                    'project__name': 'name',
                    'project__id': 'project_id',
                    'count': 'value'
                }
            ),
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False)
    def platforms(self, request, format=None):
        return Response(
            replace_keys(
                list(Computer.group_by_platform()),
                {
                    'project__platform__name': 'name',
                    'project__platform__id': 'platform_id',
                    'count': 'value'
                }
            ),
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='attributes/count')
    def attributes_count(self, request, format=None):
        attributes = request.query_params.getlist('attributes')
        project_id = request.query_params.get('project_id', None)

        return Response(
            Computer.count_by_attributes(attributes, project_id),
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='new/month')
    def new_computers_by_month(self, request, format=None):
        begin_date, end_date = month_interval()

        data = event_by_month(
            Computer.stacked_by_month(request.user.userprofile, begin_date),
            begin_date,
            end_date,
            'computer'
        )
        return Response(
            data,
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='productive/platform')
    def productive_computers_by_platform(self, request, format=None):
        data = Computer.productive_computers_by_platform(request.user.userprofile)
        inner_aliases = {
            'project__platform__id': 'platform_id',
            'project__platform__name': 'name',
            'count': 'value'
        }
        outer_aliases = {
            'project__name': 'name',
            'project__id': 'project_id',
            'project__platform__id': 'platform_id',
            'count': 'value'
        }

        return Response(
            {
                'total': data['total'],
                'inner': replace_keys(data['inner'], inner_aliases),
                'outer': replace_keys(data['outer'], outer_aliases)
            },
            status=status.HTTP_200_OK
        )
