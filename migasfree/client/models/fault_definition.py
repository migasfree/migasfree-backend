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
from django.db.models import Q
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from ...core.models import Attribute, UserProfile, MigasLink


class DomainFaultDefinitionManager(models.Manager):
    def scope(self, user):
        qs = super().get_queryset()
        if not user.is_view_all():
            user_attributes = user.get_attributes()
            qs = qs.filter(included_attributes__id__in=user_attributes)

        return qs.distinct()


class FaultDefinition(models.Model, MigasLink):
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

    language = models.IntegerField(
        verbose_name=_("programming language"),
        default=settings.MIGASFREE_PROGRAMMING_LANGUAGES[0][0],
        choices=settings.MIGASFREE_PROGRAMMING_LANGUAGES
    )

    code = models.TextField(
        verbose_name=_("code"),
        blank=True
    )

    included_attributes = models.ManyToManyField(
        Attribute,
        related_name='faultdefinition_included',
        blank=True,
        verbose_name=_("included attributes")
    )

    excluded_attributes = models.ManyToManyField(
        Attribute,
        related_name='faultdefinition_excluded',
        blank=True,
        verbose_name=_("excluded attributes")
    )

    users = models.ManyToManyField(
        UserProfile,
        related_name='faultdefinition_users',
        blank=True,
        verbose_name=_("users")
    )

    objects = DomainFaultDefinitionManager()

    def list_included_attributes(self):
        return self.included_attributes.values_list('value', flat=True)

    list_included_attributes.short_description = _("included attributes")

    def list_excluded_attributes(self):
        return self.excluded_attributes.values_list('value', flat=True)

    list_excluded_attributes.short_description = _("excluded attributes")

    def list_users(self):
        return self.users.values_list('username', flat=True)

    list_users.short_description = _("users")

    @staticmethod
    def enabled_for_attributes(attributes):
        return FaultDefinition.objects.filter(
            Q(enabled=True) &
            Q(included_attributes__id__in=attributes) &
            ~Q(excluded_attributes__id__in=attributes)
        ).distinct()

    def related_objects(self, model, user):
        """
        Returns Queryset with the related computers based in attributes
        """
        if model == 'computer':
            from .computer import Computer

            return Computer.productive.scope(user).filter(
                sync_attributes__in=self.included_attributes.all()
            ).exclude(
                sync_attributes__in=self.excluded_attributes.all()
            ).distinct()

        return None

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.code = self.code.replace("\r\n", "\n")

        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'client'
        verbose_name = _('Fault Definition')
        verbose_name_plural = _('Fault Definitions')
        ordering = ['name']
