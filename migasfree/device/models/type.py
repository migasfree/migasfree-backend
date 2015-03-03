# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _


class Type(models.Model):
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
        verbose_name = _("Device (Type)")
        verbose_name_plural = _("Device (Types)")
        permissions = (("can_save_device_type", "Can save Device Type"),)
