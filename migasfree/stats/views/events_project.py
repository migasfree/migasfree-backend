# Copyright (c) 2025-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2025-2026 Alberto Gacías <alberto@migasfree.org>
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

import locale
import time
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...client.models import Error, Fault, Migration, Synchronization
from ...utils import replace_keys
from .events import EventViewSet, event_by_day, event_by_month, month_interval


@extend_schema(tags=['stats'])
@permission_classes((permissions.IsAuthenticated,))
class EventProjectViewSet(EventViewSet):
    @action(methods=['get'], detail=False)
    def unchecked(self, request):
        event_class = self.get_event_class()
        data = event_class.unchecked_by_project(request.user.userprofile)
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

    def get_event_class(self):
        patterns = {
            'error': Error,
            'fault': Fault,
            'sync': Synchronization,
            'migration': Migration,
        }

        for pattern, event_class in patterns.items():
            if pattern in self.basename:
                return event_class

        raise ValueError('No matching event class found')

    @action(methods=['get'], detail=False, url_path='project/month')
    def project_by_month(self, request):
        begin_date, end_date = month_interval(
            begin_month=request.query_params.get('begin', ''), end_month=request.query_params.get('end', '')
        )

        event_class = self.get_event_class()

        data = event_by_month(
            event_class.stacked_by_month(request.user.userprofile, begin_date), begin_date, end_date, 'error'
        )
        return Response(data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='project/day')
    def project_by_day(self, request):
        begin_date = request.query_params.get('begin', '')
        end_date = request.query_params.get('end', '')

        locale.setlocale(locale.LC_ALL, '')  # strftime not using locale settings (python3)
        now = time.localtime()
        fmt = '%Y-%m-%d'

        try:
            end_date = timezone.make_aware(datetime.strptime(end_date, fmt))
        except ValueError:
            end_date = timezone.make_aware(datetime(now[0], now[1], now[2])) + timedelta(days=1)

        try:
            begin_date = timezone.make_aware(datetime.strptime(begin_date, fmt))
        except ValueError:
            begin_date = end_date - timedelta(days=settings.DAILY_RANGE)

        event_class = self.get_event_class()

        data = event_by_day(
            event_class.stacked_by_day(request.user.userprofile, begin_date), begin_date, end_date, 'error'
        )
        return Response(data, status=status.HTTP_200_OK)
