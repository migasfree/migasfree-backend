# -*- coding: utf-8 -*-

# Copyright (c) 2017-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2017-2021 Alberto Gacías <alberto@migasfree.org>
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
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .migas_link import MigasLink
from .package import Package
from .project import Project
from .store import Store


class DomainPackageSetManager(models.Manager):
    def scope(self, user):
        qs = super().get_queryset()
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

    def clean(self):
        super().clean()

        if not hasattr(self, 'project'):
            return False

        if self.store.project.id != self.project.id:
            raise ValidationError(_('Store must belong to the project'))

        # TODO packages must be in the same store

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'core'
        verbose_name = _('Package Set')
        verbose_name_plural = _('Package Sets')
