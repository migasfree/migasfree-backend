# -*- coding: utf-8 *-*

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from .models import (
    Device,
    Feature,
    Driver,
)


@python_2_unicode_compatible
class DeviceLogical(models.Model):
    device = models.ForeignKey(
        Device,
        verbose_name=_("device")
    )

    feature = models.ForeignKey(
        Feature,
        verbose_name=_("feature")
    )

    def datadict(self, version):
        try:
            driver = Driver.objects.filter(
                version__id=version.id,
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
            }
        }

        dictdevice = self.device.datadict()
        for key, value in dictdevice.items():
            ret[self.device.connection.devicetype.name][key] = value

        for key, value in dictdriver.items():
            ret[self.device.connection.devicetype.name][key] = value

        return ret

    def __str__(self):
        return '%s__%s__%s__%s' % (
            self.device.name,
            self.device.model.name,
            self.feature.name,
            str(self.id)
        )

    class Meta:
        app_label = 'device'
        verbose_name = _("Device (Logical)")
        verbose_name_plural = _("Device (Logical)")
        unique_together = (("device", "feature"),)
