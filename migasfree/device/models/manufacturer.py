# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _


class Manufacturer(models.Model):
    name = models.CharField(
        _("name"),
        max_length=50,
        null=True,
        blank=True,
        unique=True
    )

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'device'
        verbose_name = _("Device (Manufacturer)")
        verbose_name_plural = _("Device (Manufacturers)")
        permissions = (
            ("can_save_device_manufacturer", "Can save Device Manufacturer"),
        )
