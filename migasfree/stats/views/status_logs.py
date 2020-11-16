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

from collections import defaultdict

from django.db.models.aggregates import Count
from django.utils.translation import gettext as _
from rest_framework import status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...client.models import StatusLog, Computer

from .events import event_by_month, month_interval, EventViewSet


@permission_classes((permissions.IsAuthenticated,))
class StatusLogStatsViewSet(EventViewSet):
    @action(methods=['get'], detail=False, url_path='status')
    def by_status(self, request, format=None):
        user = request.user.userprofile
        total = StatusLog.objects.scope(user).count()

        values = defaultdict(list)
        for item in StatusLog.objects.scope(user).values(
            'status',
        ).annotate(
            count=Count('id')
        ).order_by('status', '-count'):
            values[item.get('status')].append(
                {
                    'name': _(dict(Computer.STATUS_CHOICES)[item.get('status')]),
                    'value': item.get('count'),
                    'status_in': item.get('status'),
                }
            )

        subscribed = 0
        subscribed += values['intended'][0]['value'] if 'intended' in values else 0
        subscribed += values['reserved'][0]['value'] if 'reserved' in values else 0
        subscribed += values['unknown'][0]['value'] if 'unknown' in values else 0
        subscribed += values['available'][0]['value'] if 'available' in values else 0
        subscribed += values['in repair'][0]['value'] if 'in repair' in values else 0
        unsubscribed = values['unsubscribed'][0]['value'] if 'unsubscribed' in values else 0
        data = [
            {
                'name': _('Subscribed'),
                'value': subscribed,
                'status_in': 'intended,reserved,unknown,available,in repair',
                'data': values.get('intended', []) + values.get('reserved', [])
                + values.get('unknown', []) + values.get('available', []) + values.get('in repair', [])
            },
            {
                'name': _('unsubscribed'),
                'value': unsubscribed,
                'status_in': 'unsubscribed',
                'data': values.get('unsubscribed', [])
            },
        ]

        return Response(
            {
                'title': _('Status Logs / Status'),
                'total': total,
                'data': data,
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='status/month')
    def status_by_month(self, request, format=None):
        begin_date, end_date = month_interval()

        data = event_by_month(
            StatusLog.stacked_by_month(request.user.userprofile, begin_date, field='status'),
            begin_date,
            end_date,
            'statuslog',
            field='status'
        )
        return Response(
            data,
            status=status.HTTP_200_OK
        )
