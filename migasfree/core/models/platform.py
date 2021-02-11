# -*- coding: utf-8 *-*

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

from django.db import models
from django.utils.translation import gettext_lazy as _

from .migas_link import MigasLink


class DomainPlatformManager(models.Manager):
    def scope(self, user):
        qs = super().get_queryset()
        if not user.is_view_all():
            qs = qs.filter(project__in=user.get_projects()).distinct()

        return qs


class PlatformManager(DomainPlatformManager):
    def create(self, name):
        obj = Platform()
        obj.name = name
        obj.save()

        return obj


class Platform(models.Model, MigasLink):
    """
    Computer Platform
    """

    name = models.CharField(
        verbose_name=_('name'),
        max_length=50,
        unique=True
    )

    objects = PlatformManager()

    def __str__(self):
        return self.name

    def related_objects(self, model, user):
        """
        Returns Queryset with the related computers based in project
        """
        if model == 'computer':
            from migasfree.client.models import Computer

            return Computer.productive.scope(user).filter(
                project__platform__id=self.id
            ).distinct()

        return None

    class Meta:
        app_label = 'core'
        verbose_name = _('Platform')
        verbose_name_plural = _('Platforms')
        ordering = ['name']
