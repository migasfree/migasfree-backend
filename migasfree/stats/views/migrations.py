# -*- coding: UTF-8 -*-

# Copyright (c) 2015-2022 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2022 Alberto Gacías <alberto@migasfree.org>
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

from collections import defaultdict

from django.db.models.aggregates import Count
from django.utils.translation import gettext as _
from rest_framework import status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...core.models import Platform
from ...client.models import Migration

from .events import (
    event_by_month, month_interval,
    EventViewSet,
)


@permission_classes((permissions.IsAuthenticated,))
class MigrationStatsViewSet(EventViewSet):
    @action(methods=['get'], detail=False, url_path='project')
    def by_project(self, request):
        user = request.user.userprofile
        total = Migration.objects.scope(user).count()

        values = defaultdict(list)
        for item in Migration.objects.scope(user).values(
            'project__name',
            'project__id',
            'project__platform__id'
        ).annotate(
            count=Count('id')
        ).order_by('project__platform__id', '-count'):
            values[item.get('project__platform__id')].append(
                {
                    'name': item.get('project__name'),
                    'value': item.get('count'),
                    'project_id': item.get('project__id'),
                    'platform_id': item.get('project__platform__id'),
                }
            )

        data = []
        for platform in Platform.objects.scope(user).all():
            if platform.id in values:
                count = sum(item['value'] for item in values[platform.id])
                data.append(
                    {
                        'name': platform.name,
                        'value': count,
                        'platform_id': platform.id,
                        'data': values[platform.id]
                    }
                )

        return Response(
            {
                'title': _('Migrations / Project'),
                'total': total,
                'data': data,
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='project/month')
    def project_by_month(self, request):
        begin_date, end_date = month_interval(
            begin_month=request.query_params.get('begin', ''),
            end_month=request.query_params.get('end', '')
        )

        data = event_by_month(
            Migration.stacked_by_month(request.user.userprofile, begin_date),
            begin_date,
            end_date,
            'migration'
        )
        return Response(
            data,
            status=status.HTTP_200_OK
        )
