# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _

from .models import Type, Manufacturer, Connection


class Model(models.Model):
    name = models.CharField(
        _("name"),
        max_length=50,
        null=True,
        blank=True
    )

    manufacturer = models.ForeignKey(
        Manufacturer,
        verbose_name=_("manufacturer")
    )

    device_type = models.ForeignKey(
        Type,
        verbose_name=_("type")
    )

    connections = models.ManyToManyField(
        Connection,
        null=True,
        blank=True,
        verbose_name=_("connections")
    )

    def __unicode__(self):
        return u'%s-%s' % (str(self.manufacturer), str(self.name))

    def save(self, *args, **kwargs):
        self.name = self.name.replace(" ", "_")
        super(Model, self).save(*args, **kwargs)

    class Meta:
        app_label = 'device'
        verbose_name = _("Device (Model)")
        verbose_name_plural = _("Device (Models)")
        unique_together = (("device_type", "manufacturer", "name"),)
        permissions = (("can_save_device_model", "Can save Device Model"),)
