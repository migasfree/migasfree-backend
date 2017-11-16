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
from django.utils.translation import ugettext_lazy as _

from migasfree.core.models import Project

from .event import Event


class ErrorQueryset(models.query.QuerySet):
    def unchecked(self):
        return self.filter(checked=False)


class ErrorManager(models.Manager):
    def create(self, computer, project, description):
        obj = Error()
        obj.computer = computer
        obj.project = project
        obj.description = description
        obj.save()

        return obj

    def get_queryset(self):
        return ErrorQueryset(self.model, using=self._db)

    def unchecked(self):
        return self.get_queryset().unchecked()


class Error(Event):
    description = models.TextField(
        verbose_name=_("description"),
        null=True,
        blank=True
    )

    checked = models.BooleanField(
        verbose_name=_("checked"),
        default=False,
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_("project")
    )

    objects = ErrorManager()

    def checked_ok(self):
        self.checked = True
        self.save()

    def save(self, *args, **kwargs):
        self.description = self.description.replace("\r\n", "\n")
        super(Error, self).save(*args, **kwargs)

    class Meta:
        app_label = 'client'
        verbose_name = _("Error")
        verbose_name_plural = _("Errors")
