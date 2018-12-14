# -*- coding: utf-8 -*-

# Copyright (c) 2018 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2018 Alberto Gacías <alberto@migasfree.org>
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
from django.template.defaultfilters import slugify
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from .attribute import Attribute
from .domain import Domain
from .user_profile import UserProfile


class ScopeManager(models.Manager):
    def create(self, user, name, included_attributes, excluded_attributes):
        obj = Scope()
        obj.name = name
        obj.user = user
        obj.included_attributes = included_attributes
        obj.excluded_attributes = excluded_attributes
        obj.save()
        return obj

    def scope(self, user):
        qs = super(ScopeManager, self).get_queryset()
        qs = qs.filter(user=user)
        if user.domain_preference:
            qs = qs.filter(domain=user.domain_preference)

        if not user.is_view_all():
            qs = qs.filter(included_attributes__in=user.get_attributes()).distinct()

        return qs


@python_2_unicode_compatible
class Scope(models.Model):
    user = models.ForeignKey(
        UserProfile,
        verbose_name=_('user'),
        null=False,
        on_delete=models.CASCADE,
    )

    name = models.CharField(
        max_length=50,
        verbose_name=_('name')
    )

    domain = models.ForeignKey(
        Domain,
        verbose_name=_('domain'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    included_attributes = models.ManyToManyField(
        Attribute,
        related_name='ScopeIncludedAttribute',
        blank=True,
        verbose_name=_('included attributes')
    )

    excluded_attributes = models.ManyToManyField(
        Attribute,
        related_name='ScopeExcludedAttribute',
        blank=True,
        verbose_name=_('excluded attributes')
    )

    objects = ScopeManager()

    def __str__(self):
        return self.name

    def related_objects(self, model, user):
        """
        Returns Queryset with the related computers based in attributes
        """
        if model == 'computer':
            from migasfree.client.models import Computer

            qs = Computer.productive.scope(user)
            if self.domain:
                atts_domain = Attribute.objects.filter(
                    id__in=self.domain.included_attributes.all()
                ).exclude(
                    id__in=self.domain.excluded_attributes.all()
                )
                qs = qs.filter(sync_attributes__in=atts_domain)

            qs = qs.filter(
                sync_attributes__in=self.included_attributes.all()
            ).exclude(
                sync_attributes__in=self.excluded_attributes.all()
            )

            return qs.distinct()

        return None

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.name = slugify(self.name)
        super(Scope, self).save(force_insert, force_update, using, update_fields)

    class Meta:
        app_label = 'core'
        verbose_name = _('Scope')
        verbose_name_plural = _('Scopes')
