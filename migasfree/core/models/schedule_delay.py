# -*- coding: utf-8 -*-

# Copyright (c) 2015-2017 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2017 Alberto Gacías <alberto@migasfree.org>
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
from django.core.validators import MinValueValidator
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from .schedule import Schedule
from .attribute import Attribute


@python_2_unicode_compatible
class ScheduleDelay(models.Model):
    delay = models.IntegerField(
        verbose_name=_("delay")
    )

    schedule = models.ForeignKey(
        Schedule,
        related_name='delays',
        verbose_name=_("schedule")
    )

    attributes = models.ManyToManyField(
        Attribute,
        blank=True,
        verbose_name=_("attributes")
    )

    duration = models.IntegerField(
        verbose_name=_("duration"),
        default=1,
        validators=[MinValueValidator(1), ]
    )

    def __str__(self):
        return '{} ({})'.format(self.schedule.name, self.delay)

    def attribute_list(self):
        return ', '.join(
            self.attributes.values_list('value', flat=True).order_by('value')
        )

    attribute_list.short_description = _("attribute list")

    class Meta:
        app_label = 'core'
        verbose_name = _("Schedule Delay")
        verbose_name_plural = _("Schedule Delays")
        unique_together = (("schedule", "delay"),)
