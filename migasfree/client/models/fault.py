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
from django.db.models.aggregates import Count
from django.utils.translation import gettext_lazy as _

from ...core.models import Project

from .event import Event
from .fault_definition import FaultDefinition


class DomainFaultManager(models.Manager):
    def scope(self, user):
        qs = super(DomainFaultManager, self).get_queryset()
        if user and not user.is_view_all():
            qs = qs.filter(
                project_id__in=user.get_projects(),
                computer_id__in=user.get_computers()
            )

        return qs


class UncheckedManager(DomainFaultManager):
    def get_queryset(self):
        return super(UncheckedManager, self).get_queryset().filter(
            checked=0
        )

    def scope(self, user):
        qs = super(UncheckedManager, self).scope(user).filter(checked=0)

        if user:
            qs = qs.filter(models.Q(fault_definition__users__id__in=[user.id, ])
            | models.Q(fault_definition__users=None))
        else:
            qs = qs.filter(fault_definition__users=None)

        return qs


class FaultManager(DomainFaultManager):
    def create(self, computer, definition, result):
        obj = Fault()
        obj.computer = computer
        obj.project = computer.project
        obj.fault_definition = definition
        obj.result = result
        obj.save()

        return obj


class Fault(Event):
    USER_FILTER_CHOICES = (
        ('me', _('To check for me')),
        ('only_me', _('Assigned to me')),
        ('others', _('Assigned to others')),
        ('unassigned', _('Unassigned')),
    )

    fault_definition = models.ForeignKey(
        FaultDefinition,
        on_delete=models.CASCADE,
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
        on_delete=models.CASCADE,
        verbose_name=_("project")
    )

    objects = FaultManager()
    unchecked = UncheckedManager()

    @staticmethod
    def unchecked_count(user=None):
        queryset = Fault.unchecked.scope(user)
        if user:
            queryset = queryset.filter(
                models.Q(fault_definition__users__id__in=[user.id, ])
                | models.Q(fault_definition__users=None)
            )

        return queryset.count()

    @staticmethod
    def unchecked_by_project(user):
        total = Fault.unchecked_count(user)

        projects = list(Fault.unchecked.scope(user).values(
            'project__name',
            'project__id',
            'project__platform__id',
        ).annotate(
            count=Count('id')
        ).order_by('project__platform__id', '-count'))

        platforms = list(Fault.unchecked.scope(user).values(
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
    def group_by_definition(user=None):
        return Fault.objects.scope(user).values(
            'fault_definition__id', 'fault_definition__name'
        ).annotate(
            count=models.aggregates.Count('fault_definition__id')
        ).order_by('-count')

    def checked_ok(self):
        self.checked = True
        self.save()

    def list_users(self):
        return self.fault_definition.list_users()

    class Meta:
        app_label = 'client'
        verbose_name = _("Fault")
        verbose_name_plural = _("Faults")
