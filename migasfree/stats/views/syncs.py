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

import time

from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django_redis import get_redis_connection
from rest_framework import status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...core.models import Project
from ...client.models import Synchronization
from ...utils import replace_keys
from .. import validators

from .events import (
    event_by_month, month_interval,
    month_year_iter, EventViewSet,
)

from . import DAILY_RANGE, MONTHLY_RANGE

def daterange(start_date, end_date):
    # http://stackoverflow.com/questions/1060279/iterating-through-a-range-of-dates-in-python
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


@permission_classes((permissions.IsAuthenticated,))
class SyncStatsViewSet(EventViewSet):
    @action(methods=['get'], detail=False)
    def yearly(self, request, format=None):
        """
        Returns unique number of synchronized computers
        Params:
            begin int (Y)
            end int (Y)
            project_id int
        """
        begin = int(request.query_params.get('begin', time.localtime()[0]))
        end = int(request.query_params.get('end', time.localtime()[0] + 1))
        project_id = request.query_params.get('project_id', 0)

        validators.validate_year(begin)
        validators.validate_year(end)

        key = 'migasfree:stats:years'
        if project_id:
            get_object_or_404(Project, pk=project_id)
            key = 'migasfree:stats:%d:years' % int(project_id)

        con = get_redis_connection()
        stats = []
        for i in range(begin, end):
            value = con.get('%s:%04d' % (key, i))
            stats.append([i, int(value) if value else 0])

        return Response(stats, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def monthly(self, request, format=None):
        """
        Returns unique number of synchronized computers
        Params:
            begin string (Y-m)
            end string (Y-m)
            project_id int
        """
        fmt = '%Y-%m'

        end = request.query_params.get('end', '')
        try:
            end = datetime.strptime(end, fmt)
        except ValueError:
            end = datetime.now() + relativedelta(months=1)

        begin = request.query_params.get('begin', '')
        try:
            begin = datetime.strptime(begin, fmt)
        except ValueError:
            begin = end - relativedelta(months=+MONTHLY_RANGE)

        begin += relativedelta(day=1, hour=0, minute=0, second=0, microsecond=0)

        project_id = request.query_params.get('project_id', 0)

        key = 'migasfree:stats:months'
        if project_id:
            get_object_or_404(Project, pk=project_id)
            key = 'migasfree:stats:%d:months' % int(project_id)

        con = get_redis_connection()
        stats = []
        for i in month_year_iter(
            begin.month, begin.year,
            end.month, end.year
        ):
            value = con.get('%s:%04d%02d' % (key, i[0], i[1]))
            stats.append([
                '%04d-%02d' % (i[0], i[1]),
                int(value) if value else 0
            ])

        return Response(stats, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def daily(self, request, format=None):
        """
        Returns unique number of synchronized computers
        Params:
            begin string (Y-m-d)
            end string (Y-m-d)
            project_id int
        """
        now = time.localtime()
        fmt = '%Y-%m-%d'

        end = request.query_params.get('end', '')
        try:
            end = datetime.strptime(end, fmt)
        except ValueError:
            end = datetime(now[0], now[1], now[2]) + timedelta(days=1)

        begin = request.query_params.get('begin', '')
        try:
            begin = datetime.strptime(begin, fmt)
        except ValueError:
            begin = end - timedelta(days=DAILY_RANGE)

        project_id = request.query_params.get('project_id', 0)

        key = 'migasfree:stats:days'
        if project_id:
            get_object_or_404(Project, pk=project_id)
            key = 'migasfree:stats:%d:days' % int(project_id)

        con = get_redis_connection()
        stats = []
        for single_date in daterange(begin, end):
            value = con.get('%s:%s' % (
                key,
                time.strftime('%Y%m%d', single_date.timetuple())
            ))
            stats.append([
                time.strftime(fmt, single_date.timetuple()),
                int(value) if value else 0
            ])

        return Response(stats, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def hourly(self, request, format=None):
        """
        Returns unique number of synchronized computers
        Params:
            begin string (Y-m-dTH)
            end string (Y-m-dTH)
            project_id int
        """
        now = time.localtime()
        hour = timedelta(hours=1)
        fmt = '%Y-%m-%dT%H'

        begin = request.query_params.get('begin', '')
        try:
            begin = datetime.strptime(begin, fmt)
        except ValueError:
            begin = datetime(now[0], now[1], now[2], now[3])

        end = request.query_params.get('end', '')
        try:
            end = datetime.strptime(end, fmt)
        except ValueError:
            end = datetime(now[0], now[1], now[2], now[3]) + hour

        project_id = request.query_params.get('project_id', 0)

        key = 'migasfree:stats:hours'
        if project_id:
            get_object_or_404(Project, pk=project_id)
            key = 'migasfree:stats:%d:hours' % int(project_id)

        con = get_redis_connection()
        stats = []
        while begin <= end:
            value = con.get('%s:%s' % (
                key, begin.strftime('%Y%m%d%H')
            ))
            stats.append([
                begin.strftime(fmt),
                int(value) if value else 0
            ])
            begin += hour

        return Response(stats, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='project')
    def by_project(self, request, format=None):
        return Response(
            {
                'title': _('Synchronizations / Project'),
                'total': Synchronization.objects.scope(request.user.userprofile).count(),
                'data': replace_keys(
                    list(Synchronization.group_by_project(request.user.userprofile)),
                    {
                        'project__name': 'name',
                        'project__id': 'project_id',
                        'count': 'value'
                    }
                ),
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='project/month')
    def project_by_month(self, request, format=None):
        begin_date, end_date = month_interval()

        data = event_by_month(
            Synchronization.stacked_by_month(request.user.userprofile, begin_date),
            begin_date,
            end_date,
            'synchronization'
        )
        return Response(
            data,
            status=status.HTTP_200_OK
        )
