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

import os
import shutil

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.conf import settings
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from . import Platform

from migasfree.core.pms import get_available_pms
from migasfree.core.validators import validate_project_pms


@python_2_unicode_compatible
class Project(models.Model):
    """
    OS Version: 'Ubuntu natty 32bit' or 'openSUSE 12.1' or 'Vitalinux'
    This is 'your personal distribution', a set of computers with a determinate
    Distribution for customize.
    """

    name = models.CharField(
        verbose_name=_("name"),
        max_length=50,
        unique=True
    )

    slug = models.SlugField(
        verbose_name=_("slug"),
        max_length=50,
        unique=True
    )

    pms = models.CharField(
        choices=get_available_pms(),
        max_length=50,
        verbose_name=_("package management system"),
        validators=[validate_project_pms]
    )

    architecture = models.CharField(
        verbose_name=_("architecture"),
        max_length=20
    )

    autoregister = models.BooleanField(
        verbose_name=_("autoregister"),
        default=False,
        help_text=_("Is not needed a user for register the computer in \
                     database and get the keys.")
    )

    platform = models.ForeignKey(
        Platform,
        verbose_name=_("platform")
    )

    def __str__(self):
        return self.name

    @staticmethod
    def path(name):
        return os.path.join(settings.MIGASFREE_PUBLIC_DIR, name)

    @staticmethod
    def repositories_path(name):
        return os.path.join(
            settings.MIGASFREE_PUBLIC_DIR,
            name,
            'repos'
        )

    @staticmethod
    def stores_path(name):
        return os.path.join(
            settings.MIGASFREE_PUBLIC_DIR,
            name,
            'stores'
        )

    def _create_dirs(self):
        repos = self.repositories_path(self.slug)
        if not os.path.exists(repos):
            os.makedirs(repos)

        stores = self.stores_path(self.slug)
        if not os.path.exists(stores):
            os.makedirs(stores)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        self._create_dirs()

        super(Project, self).save(*args, **kwargs)

    @staticmethod
    def get_project_names():
        return Project.objects.all().order_by('name').values_list('id', 'name')

    class Meta:
        app_label = 'core'
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")


@receiver(pre_delete, sender=Project)
def delete_project(sender, instance, **kwargs):
    path = Project.path(instance.slug)
    if os.path.exists(path):
        shutil.rmtree(path)
