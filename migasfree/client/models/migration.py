# -*- coding: utf-8 *-*

# Copyright (c) 2015-2019 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2019 Alberto Gacías <alberto@migasfree.org>
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


class DomainMigrationManager(models.Manager):
    def scope(self, user):
        qs = super(DomainMigrationManager, self).get_queryset()
        if not user.is_view_all():
            qs = qs.filter(
                project_id__in=user.get_projects(),
                computer_id__in=user.get_computers()
            )

        return qs


class MigrationManager(DomainMigrationManager):
    def create(self, computer, project):
        obj = Migration()
        obj.computer = computer
        obj.project = project
        obj.save()

        return obj


class Migration(Event):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_("project")
    )

    objects = MigrationManager()

    def __str__(self):
        return '{} ({:%Y-%m-%d %H:%M:%S}) {}'.format(
            self.computer, self.created_at, self.project
        )

    class Meta:
        app_label = 'client'
        verbose_name = _("Migration")
        verbose_name_plural = _("Migrations")
