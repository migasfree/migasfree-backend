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
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from migasfree.core.models import Attribute


@python_2_unicode_compatible
class FaultDefinition(models.Model):
    name = models.CharField(
        verbose_name=_("name"),
        max_length=50,
        unique=True
    )

    description = models.TextField(
        verbose_name=_("description"),
        null=True,
        blank=True
    )

    enabled = models.BooleanField(
        verbose_name=_("enabled"),
        default=True
    )

    language = models.CharField(
        verbose_name=_("programming language"),
        default=settings.MIGASFREE_PROGRAMMING_LANGUAGES[0],
        choices=settings.MIGASFREE_PROGRAMMING_LANGUAGES,
        max_length=20
    )

    code = models.TextField(
        verbose_name=_("code"),
        null=False,
        blank=True
    )

    included_attributes = models.ManyToManyField(
        Attribute,
        blank=True,
        verbose_name=_("included")
    )

    excluded_attributes = models.ManyToManyField(
        Attribute,
        related_name="ExcludeAttributeFaultDefinition",
        blank=True,
        verbose_name=_("excluded")
    )

    users = models.ManyToManyField(
        User,
        blank=True,
        verbose_name=_("users")
    )

    def list_included_attributes(self):
        return self.included_attributes.all().values_list('value', flat=True)

    list_included_attributes.short_description = _("included attributes")

    def list_excluded_attributes(self):
        return self.excluded_attributes.all().values_list('value', flat=True)

    list_excluded_attributes.short_description = _("excluded attributes")

    def list_users(self):
        return self.users.all().values_list('username', flat=True)

    list_users.short_description = _("users")

    @staticmethod
    def enabled_for_attributes(attributes):
        return list(FaultDefinition.objects.filter(
            Q(enabled=True) &
            Q(included_attributes__id__in=attributes) &
            ~Q(excluded_attributes__id__in=attributes)
        ).values('language', 'name', 'code'))
        # FIXME .distinct('id') NOT supported in sqlite

    def save(self, *args, **kwargs):
        self.code = self.code.replace("\r\n", "\n")

        super(FaultDefinition, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'client'
        verbose_name = _("Fault Definition")
        verbose_name_plural = _("Fault Definitions")
