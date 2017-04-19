# -*- coding: utf-8 *-*

# Copyright (c) 2015-2017 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2017 Alberto Gacías <alberto@migasfree.org>
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
        return self.name if self.name else self.feature.name

    def as_dict(self, project):
        driver_dict = {}
        try:
            driver = Driver.objects.filter(
                project__id=project.id,
                model__id=self.device.model.id,
                feature__id=self.feature.id
            )[0]
            if driver:
                driver_dict = driver.as_dict()
        except IndexError:
            pass

        ret = {
            self.device.connection.device_type.name: {
                'feature': self.get_name(),
                'id': self.id,
                'manufacturer': self.device.model.manufacturer.name
            }
        }

        device_dict = self.device.as_dict()
        for key, value in list(device_dict.items()):
            ret[self.device.connection.device_type.name][key] = value

        for key, value in list(driver_dict.items()):
            ret[self.device.connection.device_type.name][key] = value

        return ret

    def __str__(self):
        return u'{}__{}__{}__{}__{}'.format(
            self.device.model.manufacturer.name,
            self.device.model.name,
            self.feature.name,
            self.device.name,
            self.id
        )

    def save(self, *args, **kwargs):
        if isinstance(self.name, basestring):
            self.name = self.name.replace(" ", "_")

        super(Logical, self).save(*args, **kwargs)

    class Meta:
        app_label = 'device'
        verbose_name = _("Device Logical")
        verbose_name_plural = _("Devices Logical")
        unique_together = (("device", "feature"),)
