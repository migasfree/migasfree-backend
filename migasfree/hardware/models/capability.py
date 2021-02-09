# -*- coding: utf-8 -*-

# Copyright (c) 2015-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2021 Alberto Gacías <alberto@migasfree.org>
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
        verbose_name=_("hardware node")
    )

    name = models.TextField(
        verbose_name=_("name"),
        blank=True
    )  # This is the field "capability" in lshw

    description = models.TextField(
        verbose_name=_("description"),
        null=True,
        blank=True
    )

    objects = CapabilityManager()

    def __str__(self):
        ret = self.name
        if self.description:
            ret += ': {}'.format(self.description)

        return ret

    class Meta:
        app_label = 'hardware'
        verbose_name = 'Hardware Capability'
        verbose_name_plural = 'Hardware Capabilities'
        unique_together = (('name', 'node'),)
