# -*- coding: utf-8 *-*

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

from django.db import models
from django.utils.translation import ugettext_lazy as _

from .computer import Computer
from .event import Event


class StatusLogManager(models.Manager):
    def create(self, computer):
        obj = StatusLog()
        obj.computer = computer
        obj.status = computer.status
        obj.save()

        return obj


class StatusLog(Event):
    status = models.CharField(
        verbose_name=_('status'),
        max_length=20,
        null=False,
        choices=Computer.STATUS_CHOICES,
        default='intended'
    )

    objects = StatusLogManager()

    class Meta:
        app_label = 'client'
        verbose_name = _("Status Log")
        verbose_name_plural = _("Status Logs")
