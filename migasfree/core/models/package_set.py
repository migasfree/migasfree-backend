# -*- coding: utf-8 -*-

# Copyright (c) 2017 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2017 Alberto Gacías <alberto@migasfree.org>
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

from .package import Package


@python_2_unicode_compatible
class PackageSet(models.Model):
    name = models.CharField(
        verbose_name=_("name"),
        max_length=50
    )

    description = models.TextField(
        verbose_name=_("description"),
        null=True,
        blank=True
    )

    packages = models.ManyToManyField(
        Package,
        blank=True,
        verbose_name=_("packages"),
    )

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'core'
        verbose_name = _("Package Set")
        verbose_name_plural = _("Package Sets")