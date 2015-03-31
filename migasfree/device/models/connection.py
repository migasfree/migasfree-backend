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

from .type import Type


@python_2_unicode_compatible
class Connection(models.Model):
    name = models.CharField(
        verbose_name=_("name"),
        max_length=50,
        null=True,
        blank=True
    )

    fields = models.CharField(
        verbose_name=_("fields"),
        max_length=100,
        null=True,
        blank=True,
        help_text=_("Fields separated by comma")
    )

    device_type = models.ForeignKey(
        Type,
        verbose_name=_("device type")
    )

    def __str__(self):
        return '(%s) %s' % (self.device_type.name, self.name)

    class Meta:
        app_label = 'device'
        verbose_name = _("Device (Connection)")
        verbose_name_plural = _("Device (Connections)")
        unique_together = (("device_type", "name"),)
