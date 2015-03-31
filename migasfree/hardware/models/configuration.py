# -*- coding: utf-8 -*-

# Copyright (c) 2015 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015 Alberto Gacías <alberto@migasfree.org>
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
from django.utils.encoding import python_2_unicode_compatible

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


@python_2_unicode_compatible
class Configuration(models.Model):
    node = models.ForeignKey(
        Node,
        verbose_name=_("hardware node")
    )

    name = models.TextField(
        verbose_name=_("name"),
        null=False,
        blank=True
    )  # This is the field "config" in lshw

    value = models.TextField(
        verbose_name=_("value"),
        null=True,
        blank=True
    )

    objects = ConfigurationManager()

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'hardware'
        verbose_name = _("Hardware Configuration")
        verbose_name_plural = _("Hardware Configurations")
        unique_together = (("name", "node"),)
