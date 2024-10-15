# -*- coding: utf-8 -*-

# Copyright (c) 2015-2024 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2024 Alberto Gacías <alberto@migasfree.org>
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
from django.db.models import Q
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

from .migas_link import MigasLink
from .schedule import Schedule
from .attribute import Attribute


class ScheduleDelayManager(models.Manager):
    def scope(self, user):
        qs = super().get_queryset()
        if user and not user.is_view_all():
            qs = qs.filter(
                Q(attributes__in=user.get_attributes()) |
                Q(attributes__in=user.get_domain_tags())
            )

        return qs


class ScheduleDelay(models.Model, MigasLink):
    delay = models.IntegerField(
        verbose_name=_('delay'),
        db_comment='number of days from the deployment start date that the assigned attributes '
                   'will be effective (Saturdays and Sundays are not taken into account)',
    )

    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        related_name='delays',
        verbose_name=_('schedule'),
        db_comment='related schedule',
    )

    attributes = models.ManyToManyField(
        Attribute,
        blank=True,
        verbose_name=_('attributes'),
    )

    duration = models.IntegerField(
        verbose_name=_('duration'),
        default=1,
        validators=[MinValueValidator(1), ],
        db_comment='number of days to complete deployment to computers assigned to the delay',
    )

    objects = ScheduleDelayManager()

    def __str__(self):
        return f'{self.schedule.name} ({self.delay})'

    def attribute_list(self):
        return ', '.join(
            self.attributes.values_list('value', flat=True).order_by('value')
        )

    attribute_list.short_description = _("attribute list")

    def related_objects(self, model, user):
        """
        Returns Queryset with the related computers based in attributes
        """
        if model != 'computer':
            return None

        from ...client.models import Computer

        return Computer.productive.scope(user).filter(
            sync_attributes__in=self.attributes.all()
        ).distinct()

    class Meta:
        app_label = 'core'
        verbose_name = _('Schedule Delay')
        verbose_name_plural = _('Schedule Delays')
        unique_together = (('schedule', 'delay'),)
        db_table_comment = 'stores delays for schedules, specifying when assigned attributes will be effective'
