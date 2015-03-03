# -*- coding: utf-8 -*-

import json

from django.db import models
from django.utils.translation import ugettext_lazy as _

from .models import Connection, Model


class Device(models.Model):
    name = models.CharField(
        verbose_name=_("name"),
        max_length=50,
        null=True,
        blank=True,
        unique=True
    )

    model = models.ForeignKey(
        Model,
        verbose_name=_("model")
    )

    connection = models.ForeignKey(
        Connection,
        verbose_name=_("connection")
    )

    data = models.TextField(
        verbose_name=_("data"),
        null=True,
        blank=False,
        default="{}"
    )

    #FIXME qué es esto? cambiar nombre: json? model_to_dict?
    def datadict(self):
        return {
            'name': self.name,
            'model': self.model.name,
            self.connection.name: json.loads(self.data),
        }

    def __unicode__(self):
        return u'%s__%s__%s' % (
            self.name,
            self.model.name,
            self.connection.name
        )

    class Meta:
        app_label = 'device'
        verbose_name = _("Device")
        verbose_name_plural = _("Devices")
        unique_together = (("connection", "name"),)
