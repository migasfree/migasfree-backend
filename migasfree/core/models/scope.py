# -*- coding: utf-8 -*-

# Copyright (c) 2018-2024 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2018-2024 Alberto Gacías <alberto@migasfree.org>
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
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _

from .migas_link import MigasLink
from .attribute import Attribute
from .domain import Domain
from .user_profile import UserProfile


class ScopeManager(models.Manager):
    def create(self, user, name, domain, included_attributes=None, excluded_attributes=None):
        obj = Scope()
        obj.name = name
        obj.user = user
        obj.domain = domain
        obj.save()

        obj.included_attributes.set(included_attributes or [])
        obj.excluded_attributes.set(excluded_attributes or [])

        return obj

    def get_queryset(self):
        return super().get_queryset().select_related('domain', 'user')

    def scope(self, user, filter_by_user=True):
        qs = self.get_queryset()
        if filter_by_user:
            qs = qs.filter(user=user)
        if user.domain_preference:
            qs = qs.filter(domain=user.domain_preference)

        if not user.is_view_all():
            qs = qs.filter(included_attributes__in=user.get_attributes()).distinct()

        return qs


class Scope(models.Model, MigasLink):
    user = models.ForeignKey(
        UserProfile,
        verbose_name=_('user'),
        null=False,
        on_delete=models.CASCADE,
        db_comment='related user profile',
    )

    name = models.CharField(
        max_length=50,
        verbose_name=_('name'),
        db_comment='scope name',
    )

    domain = models.ForeignKey(
        Domain,
        verbose_name=_('domain'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_comment='related domain',
    )

    included_attributes = models.ManyToManyField(
        Attribute,
        related_name='scope_included',
        blank=True,
        verbose_name=_('included attributes'),
    )

    excluded_attributes = models.ManyToManyField(
        Attribute,
        related_name='scope_excluded',
        blank=True,
        verbose_name=_('excluded attributes'),
    )

    objects = ScopeManager()

    def __str__(self):
        return self.name

    def related_objects(self, model, user):
        """
        Returns Queryset with the related computers based in attributes
        """
        if model == 'computer':
            from ...client.models import Computer

            qs = Computer.productive.scope(user)
            if self.domain:
                qs = qs.filter(
                    sync_attributes__in=Attribute.objects.filter(
                        id__in=self.domain.included_attributes.all()
                    ).exclude(
                        id__in=self.domain.excluded_attributes.all()
                    )
                )

            qs = qs.filter(
                sync_attributes__in=self.included_attributes.all()
            ).exclude(
                sync_attributes__in=self.excluded_attributes.all()
            ).distinct()

            return qs

        return None

    def validate_unique(self, exclude=None):
        if Scope.objects.exclude(id=self.id).filter(
                name=self.name,
                user=self.user,
                domain__isnull=True
        ).exists():
            raise ValidationError(_("Duplicated name"))

        super().validate_unique(exclude)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.name = slugify(self.name)
        super().save(force_insert, force_update, using, update_fields)

    class Meta:
        app_label = 'core'
        verbose_name = _('Scope')
        verbose_name_plural = _('Scopes')
        unique_together = (('name', 'domain', 'user'),)
        db_table_comment = 'customizable filter that allows users to define a specific set of computers'
        ' based on attributes, simplifying tasks'
