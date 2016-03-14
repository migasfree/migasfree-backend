# -*- coding: utf-8 -*-

# Copyright (c) 2015-2016 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2016 Alberto Gacías <alberto@migasfree.org>
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

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from .connection import Connection
from .model import Model


@python_2_unicode_compatible
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

    def location(self):
        data = json.loads(self.data)
        return data.get('LOCATION', '')

    def data_to_dict(self):
        return {
            'name': self.name,
            'model': self.model.name,
            self.connection.name: json.loads(self.data),
        }

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        data = json.loads(self.data)
        if 'NAME' in data:
            data['NAME'] = data['NAME'].replace(' ', '_')
            self.data = json.dumps(data)

        super(Device, self).save(*args, **kwargs)

    class Meta:
        app_label = 'device'
        verbose_name = _("Device")
        verbose_name_plural = _("Devices")
        unique_together = (("connection", "name"),)


''' TODO
@receiver(pre_save, sender=Device)
def pre_save_device(sender, instance, **kwargs):
    if instance.id:
        old_obj = Device.objects.get(pk=instance.id)
        if old_obj.data != instance.data or \
        old_obj.name != instance.name or \
        old_obj.connection.id != instance.connection.id or \
        old_obj.model.id != instance.model.id:
            for logical_device in instance.devicelogical_set.all():
                for computer in logical_device.computer_set.all():
                    computer.remove_device_copy(logical_device.id)
'''
