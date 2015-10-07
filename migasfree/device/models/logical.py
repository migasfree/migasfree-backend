# -*- coding: utf-8 *-*

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
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from .device import Device
from .feature import Feature
from .driver import Driver


@python_2_unicode_compatible
class Logical(models.Model):
    device = models.ForeignKey(
        Device,
        verbose_name=_("device")
    )

    feature = models.ForeignKey(
        Feature,
        verbose_name=_("feature")
    )

    def datadict(self, project):
        try:
            driver = Driver.objects.filter(
                project__id=project.id,
                model__id=self.device.model.id,
                feature__id=self.feature.id
            )[0]
            if driver:
                dictdriver = driver.datadict()
        except:
            dictdriver = {}

        ret = {
            self.device.connection.devicetype.name: {
                'feature': self.feature.name,
                'id': self.id,
                'manufacturer': self.device.model.manufacturer.name
            }
        }

        dictdevice = self.device.datadict()
        for key, value in dictdevice.items():
            ret[self.device.connection.devicetype.name][key] = value

        for key, value in dictdriver.items():
            ret[self.device.connection.devicetype.name][key] = value

        return ret

    def __str__(self):
        return '%s__%s__%s__%s__%s' % (
            self.device.model.manufacturer.name,
            self.device.model.name,
            self.feature.name,
            self.device.name,
            str(self.id)
        )

    class Meta:
        app_label = 'device'
        verbose_name = _("Device (Logical)")
        verbose_name_plural = _("Device (Logical)")
        unique_together = (("device", "feature"),)
