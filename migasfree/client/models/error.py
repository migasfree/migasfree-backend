# -*- coding: utf-8 -*-

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

from django.db import models
from django.utils.translation import gettext_lazy as _

from migasfree.core.models import Project

from .event import Event


class DomainErrorManager(models.Manager):
    def scope(self, user):
        qs = super(DomainErrorManager, self).get_queryset()
        if not user.is_view_all():
            qs = qs.filter(
                project_id__in=user.get_projects(),
                computer_id__in=user.get_computers()
            )

        return qs


class UncheckedManager(DomainErrorManager):
    def get_queryset(self):
        return super(UncheckedManager, self).get_queryset().filter(
            checked=0
        )

    def scope(self, user):
        return super(UncheckedManager, self).scope(user).filter(
            checked=0
        )


class ErrorManager(DomainErrorManager):
    def create(self, computer, project, description):
        obj = Error()
        obj.computer = computer
        obj.project = project
        obj.description = description
        obj.save()

        return obj


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
    unchecked = UncheckedManager()

    @staticmethod
    def unchecked_count(user=None):
        if not user:
            return Error.unchecked.count()

        return Error.unchecked.scope(user).count()

    def checked_ok(self):
        self.checked = True
        self.save()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.description = self.description.replace("\r\n", "\n")
        super(Error, self).save(force_insert, force_update, using, update_fields)

    class Meta:
        app_label = 'client'
        verbose_name = _("Error")
        verbose_name_plural = _("Errors")
