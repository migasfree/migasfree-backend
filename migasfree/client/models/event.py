# -*- coding: utf-8 -*-

# Copyright (c) 2016-2024 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2016-2024 Alberto Gacías <alberto@migasfree.org>
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

from django.db import models
from django.db.models.aggregates import Count
from django.db.models.functions import TruncDay, TruncHour, ExtractMonth, ExtractYear
from django.utils.translation import gettext_lazy as _

from ...core.models import MigasLink
from .computer import Computer


class Event(models.Model, MigasLink):
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('date'),
        db_comment='date on which the event is created',
    )

    computer = models.ForeignKey(
        Computer,
        on_delete=models.CASCADE,
        verbose_name=_('computer'),
        db_comment='computer to which the event corresponds',
    )

    @classmethod
    def by_day(cls, computer_id, start_date, end_date, user):
        return cls.objects.scope(user).filter(
             computer__id=computer_id,
             created_at__range=(start_date, end_date)
        ).annotate(
            day=TruncDay('created_at', output_field=models.DateTimeField())
        ).values('day').order_by('-day').annotate(
            count=Count('id')
        )

    @classmethod
    def by_hour(cls, start_date, end_date, user):
        return cls.objects.scope(user).filter(
            created_at__range=(start_date, end_date)
        ).annotate(
            hour=TruncHour('created_at', output_field=models.DateTimeField())
        ).order_by('hour').values('hour').annotate(
            count=Count('computer_id', distinct=True)
        )

    @classmethod
    def by_month(cls, user, start_date, field='project_id'):
        return list(cls.objects.scope(user).filter(
            created_at__gte=start_date
        ).annotate(
            year=ExtractYear('created_at'),
            month=ExtractMonth('created_at')
        ).order_by('year', 'month', field).values('year', 'month', field).annotate(
            count=Count('id')
        ))

    @classmethod
    def stacked_by_month(cls, user, start_date, field='project_id'):
        return list(cls.objects.scope(user).filter(
            created_at__gte=start_date
        ).annotate(
            year=ExtractYear('created_at'),
            month=ExtractMonth('created_at')
        ).order_by('year', 'month', field).values('year', 'month', field).annotate(
            count=Count('id')
        ))

    @classmethod
    def situation(cls, computer_id, date, user):
        return cls.objects.scope(user).filter(
            computer__id=computer_id, created_at__lte=date
        ).order_by(
            '-created_at'
        ).first()

    @classmethod
    def time_range(cls, start_date, end_date, platform=0, project=0, range_name='month', user=None):
        items = cls.objects.scope(user).filter(
            created_at__range=(start_date, end_date)
        ).extra(
            {range_name: "date_trunc('" + range_name + "', created_at)"}
        ).values(range_name).annotate(
            count=Count('computer_id', distinct=True)
        ).order_by('-' + range_name)

        if platform:
            items = items.filter(project__platform=platform)

        if project:
            items = items.filter(project__id=project)

        return items

    def __str__(self):
        return f'{self.computer} ({self.created_at:%Y-%m-%d %H:%M:%S})'

    class Meta:
        abstract = True
