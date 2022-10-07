# -*- coding: utf-8 -*-

# Copyright (c) 2017-2022 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2017-2022 Alberto Gacías <alberto@migasfree.org>
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
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .migas_link import MigasLink
from .package import Package
from .project import Project
from .store import Store


class DomainPackageSetManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('project', 'store')

    def scope(self, user):
        qs = self.get_queryset()
        if not user.is_view_all():
            qs = qs.filter(project__in=user.get_projects())

        return qs


class PackageSet(models.Model, MigasLink):
    name = models.CharField(
        verbose_name=_("name"),
        max_length=50
    )

    description = models.TextField(
        verbose_name=_("description"),
        null=True,
        blank=True
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_("project")
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        null=True,
        verbose_name=_("store")
    )

    packages = models.ManyToManyField(
        Package,
        blank=True,
        verbose_name=_("packages"),
    )

    objects = DomainPackageSetManager()

    @staticmethod
    def path(project_name, store_name, name):
        return os.path.join(Store.path(project_name, store_name), name)

    def update_store(self, store):
        previous_store = None
        if self.store != store:
            if self.store:
                previous_store = self.store.slug

            self.store = store
            self.save()

            if previous_store:
                shutil.move(
                    self.path(self.project.slug, previous_store, self.name),
                    self.path(self.project.slug, self.store, self.name)
                )

    def clean(self):
        super().clean()

        if not hasattr(self, 'project'):
            return False

        if self.store.project.id != self.project_id:
            raise ValidationError(_('Store must belong to the project'))

        for pkg in self.packages:
            if pkg.store.id != self.store.id:
                raise ValidationError(
                    _('Package %s must be in the store %s') % (pkg.fullname, self.store.name)
                )

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'core'
        verbose_name = _('Package Set')
        verbose_name_plural = _('Package Sets')
