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
from django.utils.translation import gettext_lazy as _

from ...core.models import Project, MigasLink
from ...utils import to_list, normalize_line_breaks
from .model import Model
from .capability import Capability


class Driver(models.Model, MigasLink):
    name = models.CharField(
        verbose_name=_('name'),
        max_length=100,
        null=True,
        blank=True,
        db_comment='driver name or driver file path',
    )

    model = models.ForeignKey(
        Model,
        on_delete=models.CASCADE,
        verbose_name=_('model'),
        related_name='drivers',
        db_comment='related device model',
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_('project'),
        db_comment='related project',
    )

    capability = models.ForeignKey(
        Capability,
        on_delete=models.CASCADE,
        verbose_name=_('capability'),
        db_comment='related device capability',
    )

    packages_to_install = models.TextField(
        verbose_name=_('packages to install'),
        null=True,
        blank=True,
        db_comment='required packages for the device driver to work',
    )

    def as_dict(self):
        return {
            'driver': self.name if self.name else '',
            'packages': to_list(self.packages_to_install),
        }

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.packages_to_install = normalize_line_breaks(self.packages_to_install)

        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return self.name.split('/')[-1] if self.name else ''

    class Meta:
        app_label = 'device'
        verbose_name = _('Driver')
        verbose_name_plural = _('Drivers')
        unique_together = (('model', 'project', 'capability'),)
        ordering = ['model', 'name']
        db_table_comment = 'device drivers'
