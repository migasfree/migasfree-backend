# -*- coding: UTF-8 -*-

# Copyright (c) 2015-2016 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2016 Alberto Gacías <alberto@migasfree.org>
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

from datetime import timedelta, datetime
from dateutil import relativedelta

from django.shortcuts import get_object_or_404
from django_redis import get_redis_connection
from rest_framework import viewsets, status
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response

from migasfree.core.models import Project, Deployment
from migasfree.client.models import Computer

from . import validators


def month_year_iter(start_month, start_year, end_month, end_year):
    # http://stackoverflow.com/questions/5734438/how-to-create-a-month-iterator
    ym_start = 12 * int(start_year) + int(start_month) - 1
    ym_end = 12 * int(end_year) + int(end_month) - 1
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        yield y, m + 1


def daterange(start_date, end_date):
    # http://stackoverflow.com/questions/1060279/iterating-through-a-range-of-dates-in-python
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


class SyncStatsViewSet(viewsets.ViewSet):
    @list_route(methods=['get'])
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

        con = get_redis_connection('default')
        stats = []
        for i in range(begin, end):
            value = con.get('%s:%04d' % (key, i))
            if not value:
                value = 0
            stats.append([i, int(value)])

        return Response(stats, status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def monthly(self, request, format=None):
        fmt = '%Y%m'

        begin = request.query_params.get('begin')
        try:
            begin = datetime.strptime(begin, fmt)
        except:
            begin = datetime.now()

        end = request.query_params.get('end')
        try:
            end = datetime.strptime(end, fmt)
        except:
            end = datetime.now() + relativedelta.relativedelta(months=1)

        project_id = request.query_params.get('project_id')

        key = 'migasfree:stats:months'
        if project_id:
            get_object_or_404(Project, pk=project_id)
            key = 'migasfree:stats:%d:months' % int(project_id)

        con = get_redis_connection('default')
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

    @list_route(methods=['get'])
    def daily(self, request, format=None):
        now = time.localtime()
        fmt = '%Y%m%d'

        begin = request.query_params.get('begin')
        try:
            begin = datetime.strptime(begin, fmt)
        except:
            begin = datetime(now[0], now[1], now[2])

        end = request.query_params.get('end')
        try:
            end = datetime.strptime(end, fmt)
        except:
            end = datetime(now[0], now[1], now[2]) + timedelta(days=1)

        project_id = request.query_params.get('project_id')

        key = 'migasfree:stats:days'
        if project_id:
            get_object_or_404(Project, pk=project_id)
            key = 'migasfree:stats:%d:days' % int(project_id)

        con = get_redis_connection('default')
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

    @list_route(methods=['get'])
    def hourly(self, request, format=None):
        now = time.localtime()
        hour = timedelta(hours=1)
        fmt = '%Y%m%d%H'

        begin = request.query_params.get('begin')
        try:
            begin = datetime.strptime(begin, fmt)
        except:
            begin = datetime(now[0], now[1], now[2], now[3])

        end = request.query_params.get('end')
        try:
            end = datetime.strptime(end, fmt)
        except:
            end = datetime(now[0], now[1], now[2], now[3]) + hour

        project_id = request.query_params.get('project_id')

        key = 'migasfree:stats:hours'
        if project_id:
            get_object_or_404(Project, pk=project_id)
            key = 'migasfree:stats:%d:hours' % int(project_id)

        con = get_redis_connection('default')
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


class ComputerStatsViewSet(viewsets.ViewSet):
    @list_route(methods=['get'])
    def projects(self, request, format=None):
        return Response(
            Computer.group_by_project(),
            status=status.HTTP_200_OK
        )

    @list_route(methods=['get'])
    def platforms(self, request, format=None):
        return Response(
            Computer.group_by_platform(),
            status=status.HTTP_200_OK
        )

    @list_route(methods=['get'], url_path='attributes/count')
    def attributes_count(self, request, format=None):
        attributes = request.query_params.getlist('attributes')
        project_id = request.query_params.get('project_id', None)

        return Response(
            Computer.count_by_attributes(attributes, project_id),
            status=status.HTTP_200_OK
        )


class DeploymentStatsViewSet(viewsets.ViewSet):
    @detail_route(methods=['get'], url_path='computers/assigned')
    def assigned_computers(self, request, pk=None):
        deploy = get_object_or_404(Deployment, pk=pk)

        con = get_redis_connection('default')
        response = con.smembers(
            'migasfree:deployments:%d:computers' % deploy.id
        )

        return Response(
            list(response),
            status=status.HTTP_200_OK
        )

    @detail_route(methods=['get'], url_path='computers/status/ok')
    def computers_with_ok_status(self, request, pk=None):
        deploy = get_object_or_404(Deployment, pk=pk)

        con = get_redis_connection('default')
        response = con.smembers('migasfree:deployments:%d:ok' % deploy.id)

        return Response(
            list(response),
            status=status.HTTP_200_OK
        )

    @detail_route(methods=['get'], url_path='computers/status/error')
    def computers_with_error_status(self, request, pk=None):
        deploy = get_object_or_404(Deployment, pk=pk)

        con = get_redis_connection('default')
        response = con.smembers('migasfree:deployments:%d:error' % deploy.id)

        return Response(
            list(response),
            status=status.HTTP_200_OK
        )

    @detail_route(methods=['get'])
    def timeline(self, request, pk=None):
        deploy = get_object_or_404(Deployment, pk=pk)

        con = get_redis_connection('default')

        response = {
            'computers': {
                'assigned': con.scard(
                    'migasfree:deployments:%d:computers' % deploy.id
                ),
                'ok': con.scard('migasfree:deployments:%d:ok' % deploy.id),
                'error': con.scard('migasfree:deployments:%d:error' % deploy.id)
            },
            'schedule': deploy.schedule_timeline()
        }

        return Response(
            response,
            status=status.HTTP_200_OK
        )
