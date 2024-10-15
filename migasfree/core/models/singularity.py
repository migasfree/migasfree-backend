# -*- coding: utf-8 -*-

# Copyright (c) 2023-2024 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2023-2024 Alberto Gacías <alberto@migasfree.org>
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
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .attribute import Attribute
from .migas_link import MigasLink
from .property import Property


class SingularityManager(models.Manager):
    def scope(self, user):
        qs = super().get_queryset()
        if user and not user.is_view_all():
            qs = qs.filter(id__in=user.get_attributes()).distinct()

        return qs


class Singularity(models.Model, MigasLink):
    enabled = models.BooleanField(
        verbose_name=_('enabled'),
        default=True,
        db_comment='indicates whether singularity is enabled',
    )

    name = models.CharField(
        max_length=50,
        unique=True,
        default=None,
        verbose_name=_('name'),
        db_comment='singularity name',
    )

    property_att = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        verbose_name=_('Property'),
        db_comment='related property (formula)',
    )

    priority = models.IntegerField(
        verbose_name=_('priority'),
        db_comment='singularity priority',
    )

    included_attributes = models.ManyToManyField(
        Attribute,
        related_name='singularity_included',
        blank=True,
        verbose_name=_('included attributes'),
    )

    excluded_attributes = models.ManyToManyField(
        Attribute,
        related_name='singularity_excluded',
        blank=True,
        verbose_name=_('excluded attributes'),
    )

    language = models.IntegerField(
        verbose_name=_('programming language'),
        default=settings.MIGASFREE_PROGRAMMING_LANGUAGES[0][0],
        choices=settings.MIGASFREE_PROGRAMMING_LANGUAGES,
        db_comment='programming language in which the singularity code is written',
    )

    code = models.TextField(
        verbose_name=_('code'),
        null=True,
        blank=True,
        help_text=_("This code will execute in the client computer, and it must"
                    " put in the standard output the value of the attribute correspondent"
                    " to this property.<br>The format of this value is 'name~description',"
                    " where 'description' is optional.<br><b>Example of code:</b>"
                    "<br>#Create an attribute with the name of computer from bash<br>"
                    " echo $HOSTNAME"),
        db_comment='instructions to execute on clients to obtain attributes',
    )

    objects = SingularityManager()

    def __str__(self):
        return self.name

    def list_included_attributes(self):
        return self.included_attributes.values_list('value', flat=True)

    list_included_attributes.short_description = _('included attributes')

    def list_excluded_attributes(self):
        return self.excluded_attributes.values_list('value', flat=True)

    list_excluded_attributes.short_description = _('excluded attributes')

    class Meta:
        app_label = 'core'
        verbose_name = _('Singularity')
        verbose_name_plural = _('Singularities')
        unique_together = (('name', 'property_att', 'priority'),)
        ordering = ['property_att__name', '-priority']
        db_table_comment = 'exceptions to standard formulas used for gathering attributes from computers,'
        ' allowing different formulas to be specified based on unique computer attributes'
