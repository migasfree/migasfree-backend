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

from migasfree.client.models import Computer


@python_2_unicode_compatible
class Node(models.Model):
    parent = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        verbose_name=_("parent"),
        related_name="child"
    )

    computer = models.ForeignKey(
        Computer,
        verbose_name=_("computer")
    )

    level = width = models.IntegerField(
        _("width"),
        null=False
    )

    width = models.IntegerField(
        _("width"),
        null=True
    )

    name = models.TextField(
        verbose_name=_("id"),
        null=False,
        blank=True
    )  # This is the field "id" in lshw

    class_name = models.TextField(
        _("class"),
        null=False,
        blank=True
    )  # This is the field "class" in lshw

    enabled = models.BooleanField(
        _("enabled"),
        default=False,
    )

    claimed = models.BooleanField(
        _("claimed"),
        default=False,
    )

    description = models.TextField(
        _("description"),
        null=True,
        blank=True
    )

    vendor = models.TextField(
        _("vendor"),
        null=True,
        blank=True
    )

    product = models.TextField(
        _("product"),
        null=True,
        blank=True
    )

    version = models.TextField(
        _("version"),
        null=True,
        blank=True
    )

    serial = models.TextField(
        _("serial"),
        null=True,
        blank=True
    )

    bus_info = models.TextField(
        _("bus info"),
        null=True,
        blank=True
    )

    physid = models.TextField(
        _("physid"),
        null=True,
        blank=True
    )

    slot = models.TextField(
        _("slot"),
        null=True,
        blank=True
    )

    size = models.BigIntegerField(
        _("size"),
        null=True
    )

    capacity = models.BigIntegerField(
        _("capacity"),
        null=True
    )

    clock = models.IntegerField(
        _("clock"),
        null=True
    )

    dev = models.TextField(
        _("dev"),
        null=True,
        blank=True
    )

    icon = models.TextField(
        _("icon"),
        null=True,
        blank=True
    )

    def __str__(self):
        return self.product

    class Meta:
        app_label = 'hardware'
        verbose_name = _("Hardware Node")
        verbose_name_plural = _("Hardware Nodes")
