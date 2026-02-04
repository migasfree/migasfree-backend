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

from ...core.models import MigasLink
from .connection import Connection
from .manufacturer import Manufacturer
from .type import Type


class Model(models.Model, MigasLink):
    name = models.CharField(
        verbose_name=_('name'),
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        db_comment='device model name',
    )

    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.CASCADE,
        verbose_name=_('manufacturer'),
        db_comment='related device manufacturer',
    )

    device_type = models.ForeignKey(
        Type,
        on_delete=models.CASCADE,
        verbose_name=_('type'),
        db_comment='related device type',
    )

    connections = models.ManyToManyField(
        Connection,
        blank=True,
        verbose_name=_('connections'),
    )

    @staticmethod
    def group_by_manufacturer():
        return (
            Model.objects.values(
                'manufacturer__name',
                'manufacturer__id',
            )
            .annotate(count=models.aggregates.Count('id'))
            .order_by('-count')
        )

    @staticmethod
    def group_by_project():
        return (
            Model.objects.values('drivers__project__name', 'drivers__project__id')
            .annotate(count=models.aggregates.Count('id', distinct=True))
            .order_by('drivers__project__name')
        )

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.name = self.name.replace(' ', '_')
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    class Meta:
        app_label = 'device'
        verbose_name = _('Model')
        verbose_name_plural = _('Models')
        unique_together = (('device_type', 'manufacturer', 'name'),)
        ordering = ['manufacturer', 'name']
        db_table_comment = 'device models'
