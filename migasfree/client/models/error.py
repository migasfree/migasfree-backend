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

import re

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from migasfree.core.models import Project

from .computer import Computer


class UncheckedManager(models.Manager):
    def get_queryset(self):
        return super(UncheckedManager, self).get_queryset().filter(
            checked=0
        )


@python_2_unicode_compatible
class Error(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    computer = models.ForeignKey(
        Computer,
        verbose_name=_("computer")
    )

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
        verbose_name=_("project")
    )

    objects = models.Manager()
    unchecked = UncheckedManager()

    def truncated_desc(self):
        if len(self.description) <= 250:  #FIXME constant
            return self.description
        else:
            return self.description[:250] + ' ...'

    truncated_desc.short_description = _("Truncated description")

    @staticmethod
    def unchecked():
        return Error.objects.filter(checked=0).count()

    def checked_ok(self):
        self.checked = True
        self.save()

    def save(self, *args, **kwargs):
        self.description = self.description.replace("\r\n", "\n")
        super(Error, self).save(*args, **kwargs)

    def __str__(self):
        return '%s (%s)' % (self.computer, self.created_at)

    class Meta:
        app_label = 'client'
        verbose_name = _("Error")
        verbose_name_plural = _("Errors")
