# -*- coding: utf-8 *-*

# Copyright (c) 2015-2024 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2024 Alberto Gacías <alberto@migasfree.org>
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
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ...core.models import Attribute, MigasLink
from .device import Device
from .capability import Capability
from .driver import Driver


class LogicalManager(models.Manager):
    def create(self, device, capability, alternative_capability_name=None):
        obj = Logical(
            device=device,
            capability=capability,
            alternative_capability_name=alternative_capability_name
        )
        obj.save()

        return obj

    def get_queryset(self):
        return super().get_queryset().select_related(
            'device', 'capability'
        )

    def scope(self, user):
        qs = self.get_queryset()
        if user and not user.is_view_all():
            qs = qs.filter(
                attributes__in=user.get_attributes()
            ).distinct()

        return qs


class Logical(models.Model, MigasLink):
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        verbose_name=_('device'),
        db_comment='related device',
    )

    capability = models.ForeignKey(
        Capability,
        on_delete=models.CASCADE,
        verbose_name=_('capability'),
        db_comment='related device capability',
    )

    alternative_capability_name = models.CharField(
        verbose_name=_('alternative capability name'),
        max_length=50,
        null=True,
        blank=True,
        unique=False,
        db_comment='alternative capability name',
    )

    attributes = models.ManyToManyField(
        Attribute,
        blank=True,
        verbose_name=_('attributes'),
        help_text=_('Assigned Attributes'),
    )

    objects = LogicalManager()

    def get_name(self):
        return self.alternative_capability_name if self.alternative_capability_name else self.capability.name

    def as_dict(self, project):
        driver_as_dict = {}
        try:
            driver = Driver.objects.filter(
                project__id=project.id,
                model__id=self.device.model.id,
                capability__id=self.capability_id
            )[0]
            if driver:
                driver_as_dict = driver.as_dict()
        except IndexError:
            pass

        ret = {
            self.device.connection.device_type.name: {
                'capability': self.get_name(),
                'feature': self.get_name(),  # compatibility with client 4.x
                'id': self.id,
                'manufacturer': self.device.model.manufacturer.name
            }
        }

        device_as_dict = self.device.as_dict()
        for key, value in list(device_as_dict.items()):
            ret[self.device.connection.device_type.name][key] = value

        for key, value in list(driver_as_dict.items()):
            ret[self.device.connection.device_type.name][key] = value

        return ret

    @extend_schema_field(serializers.CharField)
    def __str__(self):
        data = json.loads(self.device.data)
        if 'NAME' in data and not (data['NAME'] == 'undefined' or data['NAME'] == ''):
            return f'{data["NAME"]}__{self.get_name()}__{self.device.name}'

        return '{}__{}__{}__{}'.format(
            self.device.model.manufacturer.name,
            self.device.model.name,
            self.get_name(),
            self.device.name,
        )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if isinstance(self.alternative_capability_name, str):
            self.alternative_capability_name = self.alternative_capability_name.replace(" ", "_")

        super().save(force_insert, force_update, using, update_fields)

    class Meta:
        app_label = 'device'
        verbose_name = _('Logical Device')
        verbose_name_plural = _('Logical Devices')
        ordering = [
            'device__model__manufacturer__name', 'device__model__name',
            'alternative_capability_name', 'capability__name', 'device__name'
        ]
        unique_together = (('device', 'capability'),)
        db_table_comment = 'logical device features'
