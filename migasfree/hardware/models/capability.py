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

from .node import Node


class CapabilityManager(models.Manager):
    def create(self, node, name, description):
        obj = Capability(
            node=node,
            name=name,
            description=description
        )
        obj.save()

        return obj


class Capability(models.Model):
    node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        verbose_name=_('hardware node'),
        db_comment='related hardware node'
    )

    name = models.TextField(
        verbose_name=_('name'),
        blank=True,
        db_comment='hardware capability name (lshw field)',
    )

    description = models.TextField(
        verbose_name=_('description'),
        null=True,
        blank=True,
        db_comment='hardware capability description',
    )

    objects = CapabilityManager()

    def __str__(self):
        ret = self.name
        if self.description:
            ret += f': {self.description}'

        return ret

    class Meta:
        app_label = 'hardware'
        verbose_name = _('Hardware Capability')
        verbose_name_plural = _('Hardware Capabilities')
        unique_together = (('name', 'node'),)
        db_table_comment = 'features and functionalities supported by the hardware components of the system'
        ' (each entry describes a specific capability, such as support for certain protocols, standards,'
        ' or performance metrics)'
