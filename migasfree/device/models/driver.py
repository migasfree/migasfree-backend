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

from migasfree.core.models import Project

from .model import Model
from .feature import Feature


@python_2_unicode_compatible
class Driver(models.Model):
    name = models.CharField(
        verbose_name=_('name'),
        max_length=100,
        null=True,
        blank=True,
    )

    model = models.ForeignKey(
        Model,
        verbose_name=_("model")
    )

    project = models.ForeignKey(
        Project,
        verbose_name=_("project")
    )

    feature = models.ForeignKey(
        Feature,
        verbose_name=_("feature")
    )

    packages_to_install = models.TextField(
        _("packages to install"),
        null=True,
        blank=True
    )

    def as_dict(self):
        lst_install = []
        for p in self.packages_to_install.replace("\r", " ").replace(
            "\n", " "
        ).split(" "):
            if p != '' and p != 'None':
                lst_install.append(p)

        return {
            'driver': self.name,
            'packages': lst_install,
        }

    def save(self, *args, **kwargs):
        self.packages_to_install = self.packages_to_install.replace(
            "\r\n", "\n"
        )
        super(Driver, self).save(*args, **kwargs)

    def __str__(self):
        return self.name.split("/")[-1]

    class Meta:
        app_label = 'device'
        verbose_name = _("Driver")
        verbose_name_plural = _("Drivers")
        unique_together = (("model", "project", "feature"),)
        ordering = ['model', 'name']
