# -*- coding: utf-8 *-*

# Copyright (c) 2015-2018 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2018 Alberto Gacías <alberto@migasfree.org>
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

import json

from past.builtins import basestring

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from migasfree.core.models import Attribute

from .device import Device
from .feature import Feature
from .driver import Driver


class LogicalManager(models.Manager):
    def create(self, device, feature, name=None):
        obj = Logical(device=device, feature=feature, name=name)
        obj.save()

        return obj

    def scope(self, user):
        qs = super(LogicalManager, self).get_queryset()
        if not user.is_view_all():
            qs = qs.filter(
                attributes__in=user.get_attributes()
            ).distinct()

        return qs


@python_2_unicode_compatible
class Logical(models.Model):
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        verbose_name=_("device")
    )

    feature = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        verbose_name=_("feature")
    )

    alternative_feature_name = models.CharField(
        verbose_name=_('alternative feature name'),
        max_length=50,
        null=True,
        blank=True,
        unique=False
    )

    attributes = models.ManyToManyField(
        Attribute,
        blank=True,
        verbose_name=_("attributes"),
        help_text=_("Assigned Attributes")
    )

    objects = LogicalManager()

    def get_name(self):
        return self.alternative_feature_name if self.alternative_feature_name else self.feature.name

    def as_dict(self, project):
        driver_as_dict = {}
        try:
            driver = Driver.objects.filter(
                project__id=project.id,
                model__id=self.device.model.id,
                feature__id=self.feature.id
            )[0]
            if driver:
                driver_as_dict = driver.as_dict()
        except IndexError:
            pass

        ret = {
            self.device.connection.device_type.name: {
                'feature': self.get_name(),
                'id': self.id,
                'manufacturer': self.device.model.manufacturer.name
            }
        }

        device_as_dict = self.device.as_dict()
        for key, value in list(device_as_dict.items()):
            ret[self.device.connection.device_type.name][key] = value

        for key, value in list(driver_as_dict.items()):
            ret[self.device.connection.device_type.name][key] = value

        return ret

    def __str__(self):
        data = json.loads(self.device.data)
        if 'NAME' in data and not (data['NAME'] == 'undefined' or data['NAME'] == ''):
            return u'{}__{}__{}'.format(
                data['NAME'],
                self.get_name(),
                self.device.name,
            )

        return u'{}__{}__{}__{}'.format(
            self.device.model.manufacturer.name,
            self.device.model.name,
            self.get_name(),
            self.device.name,
        )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if isinstance(self.alternative_feature_name, basestring):
            self.alternative_feature_name = self.alternative_feature_name.replace(" ", "_")

        super(Logical, self).save(force_insert, force_update, using, update_fields)

    class Meta:
        app_label = 'device'
        verbose_name = _("Device Logical")
        verbose_name_plural = _("Devices Logical")
        unique_together = (("device", "feature"),)
