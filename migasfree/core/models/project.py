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

import os
import shutil

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify

from ..pms import get_available_pms, get_pms
from ..validators import validate_project_pms

from . import Platform, MigasLink


class DomainProjectManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('platform')

    def scope(self, user):
        qs = self.get_queryset()
        if not user.is_view_all():
            qs = qs.filter(id__in=user.get_projects())

        return qs


class ProjectManager(DomainProjectManager):
    def create(self, name, pms, architecture, platform, auto_register_computers=False):
        obj = Project()
        obj.name = name
        obj.pms = pms
        obj.architecture = architecture
        obj.platform = platform
        obj.auto_register_computers = auto_register_computers
        obj.save()

        return obj


class Project(models.Model, MigasLink):
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

    auto_register_computers = models.BooleanField(
        verbose_name=_("auto register computers"),
        default=False,
        help_text=_("Is not needed a user for register computers in "
                    "database and get the keys.")
    )

    platform = models.ForeignKey(
        Platform,
        on_delete=models.CASCADE,
        verbose_name=_("platform")
    )

    objects = ProjectManager()

    def __str__(self):
        return self.name

    @staticmethod
    def path(name):
        return os.path.join(settings.MIGASFREE_PUBLIC_DIR, name)

    @staticmethod
    def repositories_path(name):
        return os.path.join(
            Project.path(name),
            settings.MIGASFREE_REPOSITORY_TRAILING_PATH
        )

    @staticmethod
    def stores_path(name):
        return os.path.join(
            Project.path(name),
            settings.MIGASFREE_STORE_TRAILING_PATH
        )

    def _create_dirs(self):
        repos = self.repositories_path(self.slug)
        if not os.path.exists(repos):
            os.makedirs(repos)

        stores = self.stores_path(self.slug)
        if not os.path.exists(stores):
            os.makedirs(stores)

    @staticmethod
    def get_project_names():
        return Project.objects.values_list('id', 'name').order_by('name')

    def get_pms(self):
        return get_pms(self.pms)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.slug = slugify(self.name)
        self._create_dirs()

        super().save(force_insert, force_update, using, update_fields)

    class Meta:
        app_label = 'core'
        verbose_name = _('Project')
        verbose_name_plural = _('Projects')
        ordering = ['name']


@receiver(pre_delete, sender=Project)
def delete_project(sender, instance, **kwargs):
    path = Project.path(instance.slug)
    if os.path.exists(path):
        shutil.rmtree(path)
