# -*- coding: utf-8 -*-

# Copyright (c) 2015-2016 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2016 Alberto Gacías <alberto@migasfree.org>
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
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class Property(models.Model):
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
    )

    PREFIX_LEN = 3

    prefix = models.CharField(
        verbose_name=_("prefix"),
        max_length=PREFIX_LEN,
        unique=True
    )

    name = models.CharField(
        verbose_name=_("name"),
        max_length=50
    )

    enabled = models.BooleanField(
        verbose_name=_("enabled"),
        default=True,
    )

    kind = models.CharField(
        verbose_name=_("kind"),
        max_length=1,
        default='N',
        choices=KIND_CHOICES
    )

    sort = models.CharField(
        verbose_name=_("sort"),
        max_length=10,
        default='client',
        choices=SORT_CHOICES
    )

    language = models.CharField(
        verbose_name=_("programming language"),
        default=settings.MIGASFREE_PROGRAMMING_LANGUAGES[0],
        choices=settings.MIGASFREE_PROGRAMMING_LANGUAGES,
        max_length=20
    )

    code = models.TextField(
        verbose_name=_("code"),
        null=True,
        blank=True,
        help_text=_("This code will execute in the client computer, and it must"
                    " put in the standard output the value of the attribute correspondent"
                    " to this property.<br>The format of this value is 'name~description',"
                    " where 'description' is optional.<br><b>Example of code:</b>"
                    "<br>#Create a attribute with the name of computer from bash<br>"
                    " echo $HOSTNAME")
    )

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        # Not allowed delete basic properties
        if self.sort != 'basic':
            super(Property, self).delete(*args, **kwargs)

    @staticmethod
    def enabled_client_properties():
        return list(Property.objects.filter(enabled=True).filter(
            sort='client'
        ).values('language', 'prefix', 'code'))

    class Meta:
        app_label = 'core'
        verbose_name = _("Property")
        verbose_name_plural = _("Properties")
        ordering = ['name']


class ServerProperty(Property):
    def save(self, *args, **kwargs):
        self.sort = 'server'
        self.code = ''
        super(ServerProperty, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("Stamp")
        verbose_name_plural = _("Stamps")
        proxy = True


class ClientProperty(Property):
    def save(self, *args, **kwargs):
        self.sort = 'client'
        self.code = self.code.replace("\r\n", "\n")
        super(ClientProperty, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("Formula")
        verbose_name_plural = _("Formulas")
        proxy = True


class BasicProperty(Property):
    def save(self, *args, **kwargs):
        self.sort = 'basic'
        self.code = self.code.replace("\r\n", "\n")
        super(BasicProperty, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("Basic Property")
        verbose_name_plural = _("Basic Properties")
        proxy = True
