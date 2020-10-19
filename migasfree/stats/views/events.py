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

from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta

from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext as _

from ...client.models import Computer
from ...core.models import Project

from . import MONTHLY_RANGE


def first_day_month(date_):
    return date(date_.year, date_.month, 1)


def month_year_iter(start_month, start_year, end_month, end_year):
    # http://stackoverflow.com/questions/5734438/how-to-create-a-month-iterator
    ym_start = 12 * int(start_year) + int(start_month) - 1
    ym_end = 12 * int(end_year) + int(end_month) - 1
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        yield y, m + 1


def month_interval():
    delta = relativedelta(months=+1)
    end_date = date.today() + delta
    begin_date = end_date - relativedelta(months=+MONTHLY_RANGE)

    return first_day_month(begin_date), end_date


def event_by_month(data, begin_date, end_date, model, field='project_id'):
    labels = {}
    new_data = {}
    chart_data = {}

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
            for status in Computer.STATUS_CHOICES:
                if value:
                    count = list(filter(lambda item: item['status'] == status[0], value))
                    new_data[status[0]].append({
                        'value': count[0]['count'] if count else 0,
                        'model': model,
                        'status__in': status[0],
                        'created_at__gte': start_date.strftime('%Y-%m-%d'),
                        'created_at__lt': final_date.strftime('%Y-%m-%d'),
                    })
                else:
                    new_data[status[0]].append({
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
