# Copyright (c) 2015-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2026 Alberto Gacías <alberto@migasfree.org>
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


from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from ...client.models import (
    Computer,
    Error,
    Fault,
    Migration,
    StatusLog,
    Synchronization,
)
from ...core.models import Project
from ...utils import to_heatmap

computer_id = OpenApiParameter(
    name='computer_id', location=OpenApiParameter.QUERY, default=0, description='Computer ID', type=OpenApiTypes.INT
)
start_date = OpenApiParameter(
    name='start_date',
    location=OpenApiParameter.QUERY,
    required=False,
    default='',
    description='String in YYYY-MM-DD format',
    type=OpenApiTypes.STR,
)
end_date = OpenApiParameter(
    name='end_date',
    location=OpenApiParameter.QUERY,
    required=False,
    default='',
    description='String in YYYY-MM-DD format',
    type=OpenApiTypes.STR,
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
            end_date = timezone.make_aware(datetime.strptime(f'{end_month}-01', '%Y-%m-%d'))
        except ValueError:
            end_date = date.today() + relativedelta(months=+1)

    if begin_month:
        try:
            begin_date = timezone.make_aware(datetime.strptime(f'{begin_month}-01', '%Y-%m-%d'))
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


class EventAggregator:
    def __init__(self, data, model, field='project_id', dataset_label=None):
        self.data_list = data
        self.model = model
        self.field_name = field
        self.dataset_label = dataset_label or str(model._meta.verbose_name_plural)
        self.categories = self._get_categories()
        self.data_map = self._build_data_map()

    def _get_categories(self):
        categories = {}
        if self.field_name is None:
            return {'total': self.dataset_label}
        elif self.field_name == 'project_id':
            projects = Project.objects.only('id', 'name', 'platform')
            for project in projects:
                categories[project.id] = project.name
        elif self.field_name == 'status':
            for item in Computer.STATUS_CHOICES:
                categories[item[0]] = _(item[1])
        elif self.field_name == 'checked':
            categories[True] = _('Checked')
            categories[False] = _('Unchecked')
        return categories

    def _build_data_map(self):
        """
        Builds a lookup dictionary from the data list.
        Key: (year, month, day, hour, field_value)
        """
        mapping = {}
        for item in self.data_list:
            year = item.get('year')
            month = item.get('month')
            day = item.get('day', 1)
            hour = item.get('hour', 0)
            if hasattr(hour, 'hour'):
                hour = hour.hour

            field_val = item.get(self.field_name) if self.field_name else 'total'

            key = (year, month, day, hour, field_val)
            mapping[key] = item['count']
        return mapping

    def aggregate(self, begin_date, end_date, frequency='month'):
        chart_data = {}
        new_data = {cat_id: [] for cat_id in self.categories}
        x_axis = []

        if frequency == 'month':
            iterator = month_year_iter(begin_date.month, begin_date.year, end_date.month, end_date.year)
        elif frequency == 'day':
            iterator = self._daily_iterator(begin_date, end_date)
        elif frequency == 'hour':
            iterator = datetime_iterator(begin_date, end_date - timedelta(hours=1), delta=timedelta(hours=1))

        for time_step in iterator:
            if frequency == 'month':
                year, month = time_step
                start_date = date(year, month, 1)
                final_date = start_date + relativedelta(months=+1)
                key_label = f'{year}-{month:02}'
                day = 1
                hour = 0
            elif frequency == 'day':
                start_date = time_step
                final_date = start_date + timedelta(days=1)
                key_label = start_date.strftime('%Y-%m-%d')
                year, month, day = start_date.year, start_date.month, start_date.day
                hour = 0
            elif frequency == 'hour':
                start_date = time_step
                final_date = start_date + timedelta(hours=1)
                key_label = start_date.strftime('%Y-%m-%d %H:%M:%S')
                year, month, day, hour = start_date.year, start_date.month, start_date.day, start_date.hour

            x_axis.append(key_label)

            for cat_id in self.categories:
                lookup_key = (year, month, day, hour, cat_id if self.field_name else 'total')
                count = self.data_map.get(lookup_key, 0)

                entry = {
                    'value': count,
                    'model': self.model._meta.model_name,
                    'created_at__gte': start_date.strftime('%Y-%m-%dT%H:%M:%S' if frequency == 'hour' else '%Y-%m-%d'),
                    'created_at__lt': final_date.strftime('%Y-%m-%dT%H:%M:%S' if frequency == 'hour' else '%Y-%m-%d'),
                }

                if self.field_name == 'project_id':
                    entry['project__id__exact'] = cat_id
                elif self.field_name == 'status':
                    entry['status__in'] = cat_id
                elif self.field_name == 'checked':
                    entry['checked__exact'] = 1 if cat_id else 0

                new_data[cat_id].append(entry)

        for cat_id, cat_label in self.categories.items():
            chart_data[cat_label] = new_data[cat_id]

        return {'x_labels': x_axis, 'data': chart_data}

    def _daily_iterator(self, begin_date, end_date):
        current_date = begin_date
        while current_date <= end_date:
            yield current_date
            current_date += timedelta(days=1)


def event_by_month(data, begin_date, end_date, model, field='project_id'):
    aggregator = EventAggregator(data, model, field)
    return aggregator.aggregate(begin_date, end_date, frequency='month')


def event_by_day(data, begin_date, end_date, model, field='project_id'):
    aggregator = EventAggregator(data, model, field)
    return aggregator.aggregate(begin_date, end_date, frequency='day')


@extend_schema(tags=['stats'])
@permission_classes((permissions.IsAuthenticated,))
class EventViewSet(viewsets.ViewSet):
    def get_event_class(self):
        patterns = {
            'error': Error,
            'fault': Fault,
            'sync': Synchronization,
            'migration': Migration,
            'status': StatusLog,
        }

        for pattern, event_class in patterns.items():
            if pattern in self.basename:
                return event_class

        raise NotFound('No matching event class found')

    @extend_schema(parameters=[computer_id, start_date, end_date])
    @action(methods=['get'], detail=False, url_path='by-day')
    def by_day(self, request):
        user = request.user.userprofile
        computer_id = request.GET.get('computer_id', 0)
        start_date_str = request.GET.get('start_date', '')
        end_date_str = request.GET.get('end_date', timezone.localtime().strftime('%Y-%m-%d'))
        fmt = '%Y-%m-%d'

        computer = get_object_or_404(Computer, pk=computer_id)
        if not start_date_str:
            start_date_str = timezone.localtime(computer.created_at).strftime(fmt)

        start_date = timezone.make_aware(datetime.strptime(start_date_str, fmt))
        end_date = timezone.make_aware(datetime.strptime(end_date_str, fmt))

        event_class = self.get_event_class()
        data = event_class.by_day(computer_id, start_date, end_date, user)

        return Response(to_heatmap(data), status=status.HTTP_200_OK)

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

        end = request.query_params.get('end', '')
        try:
            end = timezone.make_aware(datetime.strptime(end, fmt))
        except ValueError:
            end = timezone.make_aware(datetime(now.year, now.month, now.day, now.hour)) + timedelta(hours=1)

        begin = request.query_params.get('begin', '')
        try:
            begin = timezone.make_aware(datetime.strptime(begin, fmt))
        except ValueError:
            begin = end - timedelta(days=settings.HOURLY_RANGE)

        event_class = self.get_event_class()
        data = event_class.by_hour(begin, end, user)

        # Normalize data for EventAggregator
        # by_hour returns dicts with 'hour': datetime, 'count': int
        data_list = []
        for item in data:
            dt = item['hour']
            # Defensive check if dt is string (though usually datetime from queryset)
            if isinstance(dt, str):
                dt = timezone.make_aware(datetime.strptime(dt, fmt))

            data_list.append(
                {'year': dt.year, 'month': dt.month, 'day': dt.day, 'hour': dt.hour, 'count': item['count']}
            )

        aggregator = EventAggregator(data_list, event_class, field=None)
        return Response(aggregator.aggregate(begin, end, frequency='hour'), status=status.HTTP_200_OK)
