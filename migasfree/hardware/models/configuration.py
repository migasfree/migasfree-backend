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


class ConfigurationManager(models.Manager):
    def create(self, node, name, value):
        obj = Configuration(
            node=node,
            name=name,
            value=value
        )
        obj.save()

        return obj


class Configuration(models.Model):
    node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        verbose_name=_('hardware node'),
        db_comment='related hardware node',
    )

    name = models.TextField(
        verbose_name=_('name'),
        blank=True,
        db_comment='config field in lshw',
    )

    value = models.TextField(
        verbose_name=_('value'),
        null=True,
        blank=True,
        db_comment='hardware configuration value',
    )

    objects = ConfigurationManager()

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'hardware'
        verbose_name = _('Hardware Configuration')
        verbose_name_plural = _('Hardware Configurations')
        unique_together = (('name', 'node'),)
        db_table_comment = 'hardware node configurations'
