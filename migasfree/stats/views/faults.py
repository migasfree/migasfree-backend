# -*- coding: utf-8 -*-

# Copyright (c) 2016-2020 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2016-2020 Alberto Gacías <alberto@migasfree.org>
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
from ...client.models import Fault
from ...utils import replace_keys

from .events import event_by_month, month_interval, EventViewSet


@permission_classes((permissions.IsAuthenticated,))
class FaultStatsViewSet(EventViewSet):
    @action(methods=['get'], detail=False)
    def unchecked(self, request, format=None):
        user = request.user.userprofile
        total = Fault.unchecked_count(user)

        values = defaultdict(list)
        for item in Fault.unchecked.scope(user).values(
            'project__platform__id',
            'project__id',
            'project__name',
        ).annotate(
            count=Count('id')
        ).order_by('project__id', '-count'):
            values[item.get('project__platform__id')].append(
                {
                    'name': item.get('project__name'),
                    'value': item.get('count'),
                    'project_id': item.get('project__id'),
                    'platform_id': item.get('project__platform__id')
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
                'title': _('Unchecked Faults'),
                'total': total,
                'data': data,
            },
            status=status.HTTP_200_OK
        )


    @action(methods=['get'], detail=False, url_path='project/month')
    def project_by_month(self, request, format=None):
        begin_date, end_date = month_interval()

        data = event_by_month(
            Fault.stacked_by_month(request.user.userprofile, begin_date),
            begin_date,
            end_date,
            'fault'
        )
        return Response(
            data,
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='definition')
    def by_definition(self, request, format=None):
        user = request.user.userprofile

        return Response(
            {
                'title': _('Faults / Fault Definition'),
                'total': Fault.objects.scope(user).count(),
                'data': replace_keys(
                    list(Fault.group_by_definition(user)),
                    {
                        'fault_definition__name': 'name',
                        'fault_definition__id': 'fault_definition_id',
                        'count': 'value'
                    }
                ),
            },
            status=status.HTTP_200_OK
        )
