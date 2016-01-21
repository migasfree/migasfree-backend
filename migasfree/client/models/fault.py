# -*- coding: utf-8 -*-

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
from django.utils.encoding import python_2_unicode_compatible

from migasfree.core.models import Project

from .computer import Computer
from .fault_definition import FaultDefinition


class UncheckedManager(models.Manager):
    def get_query_set(self):
        return super(UncheckedManager, self).get_queryset().filter(
            checked=0
        )


class FaultManager(models.Manager):
    def create(self, computer, definition, result):
        fault = Fault()
        fault.computer = computer
        fault.project = computer.project
        fault.fault_definition = definition
        fault.result = result
        fault.save()

        return fault


@python_2_unicode_compatible
class Fault(models.Model):
    USER_FILTER_CHOICES = (
        ('me', _('To check for me')),
        ('only_me', _('Assigned to me')),
        ('others', _('Assigned to others')),
        ('unassigned', _('Unassigned')),
    )

    created_at = models.DateTimeField(auto_now_add=True)

    computer = models.ForeignKey(
        Computer,
        verbose_name=_("computer")
    )

    fault_definition = models.ForeignKey(
        FaultDefinition,
        verbose_name=_("fault definition")
    )

    result = models.TextField(
        verbose_name=_("result"),
        null=True,
        blank=True
    )

    checked = models.BooleanField(
        verbose_name=_("checked"),
        default=False,
    )

    project = models.ForeignKey(
        Project,
        verbose_name=_("project")
    )

    objects = FaultManager()
    unchecked = UncheckedManager()

    @staticmethod
    def unchecked():
        return Fault.objects.filter(checked=0).count()

    def checked_ok(self):
        self.checked = True
        self.save()

    def list_users(self):
        return self.fault_definition.list_users()

    def __str__(self):
        return '%s (%s)' % (self.computer, self.created_at)

    class Meta:
        app_label = 'client'
        verbose_name = _("Fault")
        verbose_name_plural = _("Faults")
