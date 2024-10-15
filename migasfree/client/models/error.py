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
from django.db.models.aggregates import Count
from django.utils.translation import gettext_lazy as _

from ...core.models import Project
from ...utils import normalize_line_breaks

from .computer import Computer
from .event import Event


class DomainErrorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'project',
            'computer',
            'computer__project',
            'computer__sync_user',
        )

    def scope(self, user):
        qs = self.get_queryset()
        if user and not user.is_view_all():
            qs = qs.filter(
                project_id__in=user.get_projects(),
                computer_id__in=user.get_computers()
            )

        return qs


class UncheckedManager(DomainErrorManager):
    def get_queryset(self):
        return super().get_queryset().filter(checked=0)

    def scope(self, user):
        return super().scope(user).filter(checked=0)


class ErrorManager(DomainErrorManager):
    def create(self, computer, project, description):
        obj = Error()
        obj.computer = computer
        obj.project = project
        obj.description = description
        obj.save()

        return obj


class Error(Event):
    TRUNCATED_DESC_LEN = 250

    description = models.TextField(
        verbose_name=_('description'),
        null=True,
        blank=True,
        db_comment='computer error description',
    )

    checked = models.BooleanField(
        verbose_name=_('checked'),
        default=False,
        db_comment='indicates whether the error has been verified or not',
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_('project'),
        db_comment='project to which the computer belongs',
    )

    objects = ErrorManager()
    unchecked = UncheckedManager()

    @staticmethod
    def unchecked_count(user=None):
        if not user:
            return Error.unchecked.count()

        return Error.unchecked.scope(user).count()

    @staticmethod
    def unchecked_by_project(user):
        total = Error.unchecked_count(user)

        projects = list(Error.unchecked.scope(user).values(
            'project__name',
            'project__id',
            'project__platform__id',
        ).annotate(
            count=Count('id')
        ).order_by('project__platform__id', '-count'))

        platforms = list(Error.unchecked.scope(user).values(
            'project__platform__id',
            'project__platform__name'
        ).annotate(
            count=Count('id')
        ).order_by('project__platform__id', '-count'))

        return {
            'total': total,
            'inner': platforms,
            'outer': projects,
        }

    @staticmethod
    def status_by_project(user):
        total = Error.objects.scope(user).count()

        projects = list(Error.objects.scope(user).values(
            'computer__status',
            'project__id',
            'project__name',
        ).annotate(
            count=Count('id')
        ).order_by('computer__status', '-count'))

        status = list(Error.objects.scope(user).values(
            'computer__status',
        ).annotate(
            count=Count('id')
        ).order_by('computer__status', '-count'))

        for item in status:
            item['status'] = item.get('computer__status')
            item['computer__status'] = _(dict(Computer.STATUS_CHOICES)[item.get('computer__status')])

        return {
            'total': total,
            'inner': status,
            'outer': projects,
        }

    def checked_ok(self):
        self.checked = True
        self.save()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.description = normalize_line_breaks(self.description)

        super().save(force_insert, force_update, using, update_fields)

    class Meta:
        app_label = 'client'
        verbose_name = _('Error')
        verbose_name_plural = _('Errors')
        db_table_comment = 'errors that occur on computers when synchronizing'
