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
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import ugettext as _
from django_redis import get_redis_connection
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ..core.models import Project, Deployment
from ..client.models import Computer
from ..utils import replace_keys

from . import validators, MONTHLY_RANGE


def month_year_iter(start_month, start_year, end_month, end_year):
    # http://stackoverflow.com/questions/5734438/how-to-create-a-month-iterator
    ym_start = 12 * int(start_year) + int(start_month) - 1
    ym_end = 12 * int(end_year) + int(end_month) - 1
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        yield y, m + 1


def first_day_month(date_):
    return date(date_.year, date_.month, 1)


def month_interval():
    delta = relativedelta(months=+1)
    end_date = date.today() + delta
    begin_date = end_date - relativedelta(months=+MONTHLY_RANGE)

    return first_day_month(begin_date), end_date


def daterange(start_date, end_date):
    # http://stackoverflow.com/questions/1060279/iterating-through-a-range-of-dates-in-python
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def event_by_month(data, begin_date, end_date, model, field='project_id'):
    labels = {}
    new_data = {}
    chart_data = {}
    url = reverse('admin:client_{}_changelist'.format(model))

    if field == 'project_id':
        projects = Project.objects.only('id', 'name')
        for project in projects:
            new_data[project.id] = []
            labels[project.id] = project.name
    elif field == 'status':
        for status in Computer.STATUS_CHOICES:
            new_data[status[0]] = []
            labels[status[0]] = _(status[1])
    elif field == 'checked':
        new_data[True] = []
        new_data[False] = []
        labels[True] = _('Checked')
        labels[False] = _('Unchecked')

    # shuffle data series
    x_axe = []
    for monthly in month_year_iter(
        begin_date.month, begin_date.year,
        end_date.month, end_date.year
    ):
        start_date = date(monthly[0], monthly[1], 1)
        final_date = start_date + relativedelta(months=+1)
        querystring = {
            'created_at__gte': start_date.strftime('%Y-%m-%d'),
            'created_at__lt': final_date.strftime('%Y-%m-%d')
        }

        key = '%d-%02d' % (monthly[0], monthly[1])
        x_axe.append(key)
        value = list(filter(lambda item: item['year'] == monthly[0] and item['month'] == monthly[1], data))
        if field == 'project_id':
            for project in projects:
                if value:
                    count = list(filter(lambda item: item['project_id'] == project.id, value))
                    querystring['project__id__exact'] = project.id
                    new_data[project.id].append({
                        'value': count[0]['count'] if count else 0,
                        'url': '{}?{}'.format(url, urlencode(querystring))
                    })
                else:
                    new_data[project.id].append({
                        'value': 0,
                        'url': '#'
                    })
        elif field == 'status':
            for status in Computer.STATUS_CHOICES:
                if value:
                    count = list(filter(lambda item: item['status'] == status[0], value))
                    querystring['status__in'] = status[0]
                    new_data[status[0]].append({
                        'value': count[0]['count'] if count else 0,
                        'url': '{}?{}'.format(url, urlencode(querystring))
                    })
                else:
                    new_data[status[0]].append({
                        'value': 0,
                        'url': '#'
                    })
        elif field == 'checked':
            for val in [True, False]:
                if value:
                    count = list(filter(lambda item: item['checked'] == val, value))
                    querystring['checked__exact'] = 1 if val else 0
                    new_data[val].append({
                        'value': count[0]['count'] if count else 0,
                        'url': '{}?{}'.format(url, urlencode(querystring))
                    })
                else:
                    new_data[val].append({
                        'value': 0,
                        'url': '#'
                    })

    for item in new_data:
        chart_data[labels[item]] = new_data[item]

    return {'x_labels': x_axe, 'data': chart_data}


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


@permission_classes((permissions.IsAuthenticated,))
class DeploymentStatsViewSet(viewsets.ViewSet):
    @action(methods=['get'], detail=True, url_path='computers/assigned')
    def assigned_computers(self, request, pk=None):
        deploy = get_object_or_404(Deployment, pk=pk)

        con = get_redis_connection()
        response = con.smembers(
            'migasfree:deployments:%d:computers' % deploy.id
        )

        return Response(
            list(response),
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True, url_path='computers/status/ok')
    def computers_with_ok_status(self, request, pk=None):
        deploy = get_object_or_404(Deployment, pk=pk)

        con = get_redis_connection()
        response = con.smembers('migasfree:deployments:%d:ok' % deploy.id)

        return Response(
            list(response),
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True, url_path='computers/status/error')
    def computers_with_error_status(self, request, pk=None):
        deploy = get_object_or_404(Deployment, pk=pk)

        con = get_redis_connection()
        response = con.smembers('migasfree:deployments:%d:error' % deploy.id)

        return Response(
            list(response),
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True)
    def timeline(self, request, pk=None):
        deploy = get_object_or_404(Deployment, pk=pk)

        con = get_redis_connection()

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
