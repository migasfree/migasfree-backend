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
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...core.models import Project
from ...client.models import Synchronization
from ...utils import replace_keys
from .. import validators

from .events import event_by_month, month_interval, month_year_iter


def daterange(start_date, end_date):
    # http://stackoverflow.com/questions/1060279/iterating-through-a-range-of-dates-in-python
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


@permission_classes((permissions.IsAuthenticated,))
class SyncStatsViewSet(viewsets.ViewSet):
    @action(methods=['get'], detail=False)
    def yearly(self, request, format=None):
        begin = int(request.query_params.get('begin', time.localtime()[0]))
        end = int(request.query_params.get('end', time.localtime()[0] + 1))
        project_id = request.query_params.get('project_id')

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
            if not value:
                value = 0
            stats.append([i, int(value)])

        return Response(stats, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def monthly(self, request, format=None):
        fmt = '%Y%m'

        begin = request.query_params.get('begin', '')
        try:
            begin = datetime.strptime(begin, fmt)
        except ValueError:
            begin = datetime.now()

        begin += relativedelta(day=1, hour=0, minute=0, second=0, microsecond=0)

        end = request.query_params.get('end', '')
        try:
            end = datetime.strptime(end, fmt)
        except ValueError:
            end = datetime.now() + relativedelta.relativedelta(months=1)

        project_id = request.query_params.get('project_id')

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
            if not value:
                value = 0
            stats.append([int('%04d%02d' % (i[0], i[1])), int(value)])

        return Response(stats, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def daily(self, request, format=None):
        now = time.localtime()
        fmt = '%Y%m%d'

        begin = request.query_params.get('begin', '')
        try:
            begin = datetime.strptime(begin, fmt)
        except ValueError:
            begin = datetime(now[0], now[1], now[2])

        end = request.query_params.get('end', '')
        try:
            end = datetime.strptime(end, fmt)
        except ValueError:
            end = datetime(now[0], now[1], now[2]) + timedelta(days=1)

        project_id = request.query_params.get('project_id')

        key = 'migasfree:stats:days'
        if project_id:
            get_object_or_404(Project, pk=project_id)
            key = 'migasfree:stats:%d:days' % int(project_id)

        con = get_redis_connection()
        stats = []
        for single_date in daterange(begin, end):
            value = con.get('%s:%s' % (
                key, time.strftime('%Y%m%d', single_date.timetuple())
            ))
            if not value:
                value = 0
            stats.append([
                int(time.strftime('%Y%m%d', single_date.timetuple())),
                int(value)
            ])

        return Response(stats, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def hourly(self, request, format=None):
        now = time.localtime()
        hour = timedelta(hours=1)
        fmt = '%Y%m%d%H'

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

        project_id = request.query_params.get('project_id')

        key = 'migasfree:stats:hours'
        if project_id:
            get_object_or_404(Project, pk=project_id)
            key = 'migasfree:stats:%d:hours' % int(project_id)

        con = get_redis_connection()
        stats = []
        while begin <= end:
            value = con.get('%s:%s' % (
                key, begin.strftime(fmt)
            ))
            if not value:
                value = 0
            stats.append([
                int(begin.strftime(fmt)),
                int(value)
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
