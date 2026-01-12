# Copyright (c) 2015-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2026 Alberto Gacías <alberto@migasfree.org>
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

from ...core.models import Project
from .event import Event


class DomainMigrationManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                'project',
                'computer',
                'computer__project',
                'computer__sync_user',
            )
        )

    def scope(self, user):
        qs = self.get_queryset()
        if user and not user.is_view_all():
            qs = qs.filter(project_id__in=user.get_projects(), computer_id__in=user.get_computers())

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
        verbose_name=_('project'),
        db_comment='project to which the computer has been migrated',
    )

    objects = MigrationManager()

    def __str__(self):
        return f'{self.computer} ({self.created_at:%Y-%m-%d %H:%M:%S}) {self.project}'

    class Meta:
        app_label = 'client'
        verbose_name = _('Migration')
        verbose_name_plural = _('Migrations')
        db_table_comment = 'switching computer projects'
