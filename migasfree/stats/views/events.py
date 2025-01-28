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

import time

from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...client.models import (
    Computer, Error, Fault,
    Synchronization, Migration, StatusLog,
)
from ...core.models import Project
from ...utils import to_heatmap

computer_id = OpenApiParameter(
    name='computer_id', location=OpenApiParameter.QUERY,
    default=0, description='Computer ID', type=OpenApiTypes.INT
)
start_date = OpenApiParameter(
    name='start_date', location=OpenApiParameter.QUERY,
    required=False, default='', description='String in YYYY-MM-DD format', type=OpenApiTypes.STR
)
end_date = OpenApiParameter(
    name='end_date', location=OpenApiParameter.QUERY,
    required=False, default='', description='String in YYYY-MM-DD format', type=OpenApiTypes.STR
)


def first_day_month(date_):
    return date(date_.year, date_.month, 1)


def datetime_iterator(from_date=None, to_date=None, delta=timedelta(minutes=1)):
    # from https://www.ianlewis.org/en/python-date-range-iterator
    from_date = from_date or timezone.localtime(timezone.now())
    while to_date is None or from_date <= to_date:
        yield from_date
        from_date += delta


def month_year_iter(start_month, start_year, end_month, end_year):
    # http://stackoverflow.com/questions/5734438/how-to-create-a-month-iterator
    ym_start = 12 * int(start_year) + int(start_month) - 1
    ym_end = 12 * int(end_year) + int(end_month) - 1
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        yield y, m + 1


def month_interval(begin_month='', end_month=''):
    # begin_month, end_month format: YYYY-MM
    if end_month:
        try:
            end_date = datetime.strptime(f'{end_month}-01', '%Y-%m-%d')
        except ValueError:
            end_date = date.today() + relativedelta(months=+1)

    if begin_month:
        try:
            begin_date = datetime.strptime(f'{begin_month}-01', '%Y-%m-%d')
            if not end_month:
                end_date = begin_date + relativedelta(months=+settings.MONTHLY_RANGE)
        except ValueError:
            if not end_month:
                end_date = date.today() + relativedelta(months=+1)

            begin_date = end_date - relativedelta(months=+settings.MONTHLY_RANGE)

    if not end_month and not begin_month:
        end_date = date.today() + relativedelta(months=+1)
        begin_date = end_date - relativedelta(months=+settings.MONTHLY_RANGE)

    if begin_date > end_date:
        begin_date, end_date = end_date, begin_date

    return first_day_month(begin_date), end_date


def event_by_month(data, begin_date, end_date, model, field='project_id'):
    labels = {}
    new_data = {}
    chart_data = {}

    if field == 'project_id':
        projects = Project.objects.only('id', 'name', 'platform')
        for project in projects:
            new_data[project.id] = []
            labels[project.id] = project.name
    elif field == 'status':
        for item in Computer.STATUS_CHOICES:
            new_data[item[0]] = []
            labels[item[0]] = _(item[1])
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

        key = f'{monthly[0]}-{monthly[1]:02}'
        x_axe.append(key)
        value = list(filter(lambda item: item['year'] == monthly[0] and item['month'] == monthly[1], data))
        if field == 'project_id':
            for project in projects:
                if value:
                    count = list(filter(lambda item: item['project_id'] == project.id, value))
                    new_data[project.id].append({
                        'value': count[0]['count'] if count else 0,
                        'model': model,
                        'project__id__exact': project.id,
                        'created_at__gte': start_date.strftime('%Y-%m-%d'),
                        'created_at__lt': final_date.strftime('%Y-%m-%d'),
                    })
                else:
                    new_data[project.id].append({
                        'value': 0,
                    })
        elif field == 'status':
            for item in Computer.STATUS_CHOICES:
                if value:
                    count = list(filter(lambda row: row['status'] == item[0], value))
                    new_data[item[0]].append({
                        'value': count[0]['count'] if count else 0,
                        'model': model,
                        'status__in': item[0],
                        'created_at__gte': start_date.strftime('%Y-%m-%d'),
                        'created_at__lt': final_date.strftime('%Y-%m-%d'),
                    })
                else:
                    new_data[item[0]].append({
                        'value': 0,
                    })
        elif field == 'checked':
            for val in [True, False]:
                if value:
                    count = list(filter(lambda item: item['checked'] == val, value))
                    new_data[val].append({
                        'value': count[0]['count'] if count else 0,
                        'model': model,
                        'checked__exact': 1 if val else 0,
                        'created_at__gte': start_date.strftime('%Y-%m-%d'),
                        'created_at__lt': final_date.strftime('%Y-%m-%d'),
                    })
                else:
                    new_data[val].append({
                        'value': 0,
                    })

    for item in new_data:
        chart_data[labels[item]] = new_data[item]

    return {'x_labels': x_axe, 'data': chart_data}


def event_by_day(data, begin_date, end_date, model, field='project_id'):
    labels = {}
    new_data = {}
    chart_data = {}

    if field == 'project_id':
        projects = Project.objects.only('id', 'name', 'platform')
        for project in projects:
            new_data[project.id] = []
            labels[project.id] = project.name
    elif field == 'status':
        for item in Computer.STATUS_CHOICES:
            new_data[item[0]] = []
            labels[item[0]] = _(item[1])
    elif field == 'checked':
        new_data[True] = []
        new_data[False] = []
        labels[True] = _('Checked')
        labels[False] = _('Unchecked')

    date_range = []
    current_date = begin_date
    while current_date <= end_date:
        date_range.append(current_date)
        current_date += timedelta(days=1)

    x_axe = [date.strftime('%Y-%m-%d') for date in date_range]

    for date in date_range:
        start_date = date
        end_of_day = date + timedelta(days=1)  # range [start, end)

        key = start_date.strftime('%Y-%m-%d')

        if field == 'project_id':
            for project in projects:
                value = list(filter(
                    lambda item:
                        item['year'] == start_date.year and
                        item['month'] == start_date.month and
                        item['day'] == start_date.day,
                    data
                ))

                count = list(filter(lambda item: item['project_id'] == project.id, value))
                new_data[project.id].append({
                    'value': count[0]['count'] if count else 0,
                    'model': model,
                    'project__id__exact': project.id,
                    'created_at__gte': start_date.strftime('%Y-%m-%d'),
                    'created_at__lt': end_of_day.strftime('%Y-%m-%d'),
                })
        elif field == 'status':
            for item in Computer.STATUS_CHOICES:
                value = list(filter(
                    lambda item:
                        item['year'] == start_date.year and
                        item['month'] == start_date.month and
                        item['day'] == start_date.day,
                    data
                ))

                count = list(filter(lambda row: row['status'] == item[0], value))
                new_data[item[0]].append({
                    'value': count[0]['count'] if count else 0,
                    'model': model,
                    'status__in': item[0],
                    'created_at__gte': start_date.strftime('%Y-%m-%d'),
                    'created_at__lt': end_of_day.strftime('%Y-%m-%d'),
                })
        elif field == 'checked':
            for val in [True, False]:
                value = list(filter(
                    lambda item:
                        item['year'] == start_date.year and
                        item['month'] == start_date.month and
                        item['day'] == start_date.day,
                    data
                ))

                count = list(filter(lambda item: item['checked'] == val, value))
                new_data[val].append({
                    'value': count[0]['count'] if count else 0,
                    'model': model,
                    'checked__exact': 1 if val else 0,
                    'created_at__gte': start_date.strftime('%Y-%m-%d'),
                    'created_at__lt': end_of_day.strftime('%Y-%m-%d'),
                })

    for item in new_data:
        chart_data[labels[item]] = new_data[item]

    return {'x_labels': x_axe, 'data': chart_data}


@permission_classes((permissions.IsAuthenticated,))
class EventViewSet(viewsets.ViewSet):
    def get_event_class(self):
        patterns = {
            'error': 'Error',
            'fault': 'Fault',
            'sync': 'Synchronization',
            'migration': 'Migration',
            'status': 'StatusLog',
        }

        for pattern, event_class in patterns.items():
            if pattern in self.basename:
                return globals()[event_class]

        raise ValueError('No matching event class found')

    @extend_schema(parameters=[computer_id, start_date, end_date])
    @action(methods=['get'], detail=False, url_path='by-day')
    def by_day(self, request):
        user = request.user.userprofile
        computer_id = request.GET.get('computer_id', 0)
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', date.today().strftime('%Y-%m-%d'))

        computer = get_object_or_404(Computer, pk=computer_id)
        if not start_date:
            start_date = computer.created_at.strftime('%Y-%m-%d')

        event_class = self.get_event_class()
        data = event_class.by_day(computer_id, start_date, end_date, user)

        return Response(
            to_heatmap(data),
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False)
    def history(self, request):
        """
        Returns events history by hours
        Params:
            begin string (Y-m-dTH)
            end string (Y-m-dTH)
        """
        user = request.user.userprofile
        now = timezone.localtime(timezone.now())
        fmt = '%Y-%m-%dT%H'
        human_fmt = '%Y-%m-%d %H:%M:%S'
        value_fmt = '%Y-%m-%dT%H:%M:%S'

        end = request.query_params.get('end', '')
        try:
            end = datetime.strptime(end, fmt)
        except ValueError:
            end = datetime(now.year, now.month, now.day, now.hour) + timedelta(hours=1)

        begin = request.query_params.get('begin', '')
        try:
            begin = datetime.strptime(begin, fmt)
        except ValueError:
            begin = end - timedelta(days=settings.HOURLY_RANGE)

        event_class = self.get_event_class()
        events = {
            i['hour'].strftime(human_fmt): i['count']
            for i in event_class.by_hour(begin, end, user)
        }

        labels = []
        stats = []

        for item in datetime_iterator(begin, end - timedelta(hours=1), delta=timedelta(hours=1)):
            next_item = item + timedelta(hours=1)
            labels.append(time.strftime(human_fmt, item.timetuple()))
            stats.append({
                'model': event_class._meta.model_name,
                'created_at__gte': time.strftime(value_fmt, item.timetuple()),
                'created_at__lt': time.strftime(value_fmt, next_item.timetuple()),
                'value': events[str(item)] if str(item) in events else 0
            })

        return Response(
            {
                'x_labels': labels,
                'data': {str(event_class._meta.verbose_name_plural): stats}
            },
            status=status.HTTP_200_OK
        )
