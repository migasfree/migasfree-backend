# -*- coding: utf-8 -*-

# Copyright (c) 2015-2025 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2025 Alberto Gacías <alberto@migasfree.org>
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

from .migas_link import MigasLink
from ...utils import normalize_line_breaks


class ClientPropertyManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(sort__in=['client', 'basic'])


class ServerPropertyManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(sort='server')


class Property(models.Model, MigasLink):
    SORT_CHOICES = (
        ('basic', _('Basic')),
        ('client', _('Client')),
        ('server', _('Server')),
    )

    KIND_CHOICES = (
        ('N', _('Normal')),
        ('-', _('List')),
        ('L', _('Added to the left')),
        ('R', _('Added to the right')),
        ('J', _('JSON')),
    )

    PREFIX_LEN = 3

    prefix = models.CharField(
        verbose_name=_('prefix'),
        max_length=PREFIX_LEN,
        unique=True,
        db_comment='it is a combination of three numbers or letters (used to group and identify attributes)',
    )

    name = models.CharField(
        verbose_name=_('name'),
        max_length=50,
        db_comment='property (formula) name',
    )

    enabled = models.BooleanField(
        verbose_name=_('enabled'),
        default=True,
        db_comment='indicates whether the property (formula) is enabled'
                   ' (if false, it will not be executed on the clients)',
    )

    kind = models.CharField(
        verbose_name=_('kind'),
        max_length=1,
        default='N',
        choices=KIND_CHOICES,
        db_comment='property (formula) kind: normal, list, added to the left, added to the right',
    )

    sort = models.CharField(
        verbose_name=_('sort'),
        max_length=10,
        default='client',
        choices=SORT_CHOICES,
        db_comment='property (formula) sort: basic (attribute), client (attribute), server (tag)',
    )

    auto_add = models.BooleanField(
        verbose_name=_('automatically add'),
        default=True,
        help_text=_('automatically add the attribute to database'),
        db_comment='automatically add the attribute to database',
    )

    language = models.IntegerField(
        verbose_name=_('programming language'),
        default=settings.MIGASFREE_PROGRAMMING_LANGUAGES[0][0],
        choices=settings.MIGASFREE_PROGRAMMING_LANGUAGES,
        db_comment='programming language in which the property (formula) code is written',
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

    def __str__(self):
        return str(self.name)

    def delete(self, using=None, keep_parents=False):
        # Not allowed delete basic properties
        if self.sort != 'basic':
            super().delete(using, keep_parents)

    @staticmethod
    def enabled_client_properties(attributes):
        from .singularity import Singularity

        client_properties = []
        for item in Property.objects.filter(enabled=True, sort='client'):
            singularities = Singularity.objects.filter(
                property_att__id=item.id,
                enabled=True,
                included_attributes__id__in=attributes,
            ).filter(
                ~models.Q(excluded_attributes__id__in=attributes)
            ).order_by('-priority')
            if singularities.count():
                client_properties.append({
                    'prefix': item.prefix,
                    'language': singularities.first().get_language_display(),
                    'code': singularities.first().code,
                })
            else:
                client_properties.append({
                    'prefix': item.prefix,
                    'language': item.get_language_display(),
                    'code': item.code,
                })

        return client_properties

    class Meta:
        app_label = 'core'
        verbose_name = _('Property')
        verbose_name_plural = _('Properties')
        ordering = ['name']
        db_table_comment = 'formulas used to gather attributes from computers'


class ServerProperty(Property):
    objects = ServerPropertyManager()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.sort = 'server'
        self.code = ''
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    class Meta:
        verbose_name = _('Stamp')
        verbose_name_plural = _('Stamps')
        proxy = True


class ClientProperty(Property):
    objects = ClientPropertyManager()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.sort = 'client'
        self.code = normalize_line_breaks(self.code)

        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    class Meta:
        verbose_name = _('Formula')
        verbose_name_plural = _('Formulas')
        proxy = True


class BasicProperty(Property):
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.sort = 'basic'
        self.code = normalize_line_breaks(self.code)

        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    class Meta:
        verbose_name = _('Basic Property')
        verbose_name_plural = _('Basic Properties')
        proxy = True
