# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _

from migasfree.core.models import Version
from .models import Model, Feature


class Driver(models.Model):
    name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    model = models.ForeignKey(
        Model,
        verbose_name=_("model")
    )

    version = models.ForeignKey(
        Version,
        verbose_name=_("version")
    )

    feature = models.ForeignKey(
        Feature,
        verbose_name=_("feature")
    )

    install = models.TextField(
        _("packages to install"),
        null=True,
        blank=True
    )

    def datadict(self):
        lst_install = []
        for p in self.install.replace("\r", " ").replace("\n", " ").split(" "):
            if p != '' and p != 'None':
                lst_install.append(p)

        return {
            'driver': self.name,
            'packages': lst_install,
        }

    def save(self, *args, **kwargs):
        self.install = self.install.replace("\r\n", "\n")
        super(Driver, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'%s' % (str(self.name).split("/")[-1])

    class Meta:
        app_label = 'device'
        verbose_name = _("Device (Driver)")
        verbose_name_plural = _("Device (Driver)")
        permissions = (("can_save_device_driver", "Can save Device Driver"),)
        unique_together = (("model", "version", "feature"),)
