# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _

from .models import Type


class Connection(models.Model):
    name = models.CharField(
        _("name"),
        max_length=50,
        null=True,
        blank=True
    )

    fields = models.CharField(
        _("fields"),
        max_length=100,
        null=True,
        blank=True,
        help_text=_("Fields separated by comma")
    )

    device_type = models.ForeignKey(
        Type,
        verbose_name=_("device type")
    )

    def __unicode__(self):
        return u'(%s) %s' % (self.device_type.name, self.name)

    class Meta:
        app_label = 'device'
        verbose_name = _("Device (Connection)")
        verbose_name_plural = _("Device (Connections)")
        unique_together = (("device_type", "name"),)
        permissions = (
            ("can_save_device_connection", "Can save Device Connection"),
        )
