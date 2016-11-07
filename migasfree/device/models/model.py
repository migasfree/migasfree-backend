# -*- coding: utf-8 -*-

# Copyright (c) 2015-2016 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2016 Alberto Gacías <alberto@migasfree.org>
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

from .type import Type
from .manufacturer import Manufacturer
from .connection import Connection


@python_2_unicode_compatible
class Model(models.Model):
    name = models.CharField(
        verbose_name=_("name"),
        max_length=50,
        null=True,
        blank=True
    )

    manufacturer = models.ForeignKey(
        Manufacturer,
        verbose_name=_("manufacturer")
    )

    device_type = models.ForeignKey(
        Type,
        verbose_name=_("type")
    )

    connections = models.ManyToManyField(
        Connection,
        blank=True,
        verbose_name=_("connections")
    )

    def __str__(self):
        return '%s-%s' % (self.manufacturer, self.name)

    def save(self, *args, **kwargs):
        self.name = self.name.replace(" ", "_")
        super(Model, self).save(*args, **kwargs)

    class Meta:
        app_label = 'device'
        verbose_name = _("Model")
        verbose_name_plural = _("Models")
        unique_together = (("device_type", "manufacturer", "name"),)
        ordering = ['manufacturer', 'name']
