# -*- coding: utf-8 -*-

# Copyright (c) 2015-2017 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2017 Alberto Gacías <alberto@migasfree.org>
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

from .project import Project


@python_2_unicode_compatible
class Store(models.Model):
    """
    Location where packages will be stored (p.e. /debian8/third/syntevo/)
    """

    name = models.CharField(
        verbose_name=_("name"),
        max_length=50
    )

    slug = models.SlugField(
        verbose_name=_("slug"),
        max_length=50,
        unique=True
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_("project")
    )

    @staticmethod
    def path(project_name, name):
        return os.path.join(
            settings.MIGASFREE_PUBLIC_DIR,
            project_name,
            Project.STORE_TRAILING_PATH,
            name
        )

    def _create_dir(self):
        path = self.path(self.project.slug, self.slug)
        if not os.path.exists(path):
            os.makedirs(path)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        self._create_dir()

        super(Store, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'core'
        verbose_name = _('Store')
        verbose_name_plural = _('Stores')
        unique_together = (('name', 'project'),)
        ordering = ['name', 'project']


@receiver(pre_delete, sender=Store)
def delete_store(sender, instance, **kwargs):
    path = Store.path(instance.project.slug, instance.slug)
    if os.path.exists(path):
        shutil.rmtree(path)
