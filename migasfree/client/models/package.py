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
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from migasfree.core.models import Project


class PackageManager(models.Manager):
    def create(self, fullname, name, version, architecture, project):
        package = Package(
            fullname=package,
            name=name,
            version=version,
            architecture=architecture,
            project=project
        )
        package.save()

        return package


@python_2_unicode_compatible
class Package(models.Model):
    """packages installed in computers"""

    fullname = models.CharField(
        verbose_name=_('fullname'),
        max_length=140,
        null=False,
        unique=True
    )

    name = models.CharField(
        verbose_name=_('name'),
        max_length=100,
        null=False,
        blank=True,
        unique=False
    )

    version = models.CharField(
        verbose_name=_('version'),
        max_length=20,
        null=False,
        unique=False
    )

    architecture = models.CharField(
        verbose_name=_('architecture'),
        max_length=10,
        null=False,
    )

    project = models.ForeignKey(
        Project,
        verbose_name=_("project"),
        related_name='+'
    )

    @staticmethod
    def normalized_name(package_name):
        name = version = architecture = None

        # name_version_architecture.ext convention
        try:
            name, version, architecture = package_name.split('_')
        except:
            if package_name.count('_') > 2:
                slices = package_name.split('_', 1)
                name = slices[0]
                version, architecture = slices[1].rsplit('_', 1)
                architecture = architecture.split('.')[0]

        return (name, version, architecture)

    def __str__(self):
        return self.fullname

    class Meta:
        app_label = 'client'
        verbose_name = _("Package")
        verbose_name_plural = _("Packages")
        unique_together = (('fullname', 'project'),)
