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

from django.db import models
from django.utils.translation import gettext_lazy as _

from ...core.models import MigasLink


class DomainUserManager(models.Manager):
    def scope(self, user):
        qs = super().get_queryset()
        if not user.is_view_all():
            qs = qs.filter(computer__in=user.get_computers())

        return qs.distinct()


class UserManager(DomainUserManager):
    def create(self, name, fullname=''):
        obj = User()
        obj.name = name
        obj.fullname = fullname
        obj.save()

        return obj


class User(models.Model, MigasLink):
    name = models.CharField(
        verbose_name=_('name'),
        max_length=50,
        null=False
    )

    fullname = models.CharField(
        verbose_name=_('fullname'),
        max_length=100,
        blank=True
    )

    objects = UserManager()

    def update_fullname(self, fullname):
        self.fullname = fullname
        self.save()

    def __str__(self):
        if self.fullname.strip():
            return '{} ({})'.format(self.name, self.fullname.strip())

        return self.name

    class Meta:
        app_label = 'client'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        unique_together = (('name', 'fullname'),)
