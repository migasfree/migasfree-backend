# -*- coding: utf-8 -*-

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

from ...core.models import Attribute, MigasLink
from ...utils import swap_m2m
from .connection import Connection
from .model import Model


class DeviceManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'connection', 'connection__device_type',
            'model', 'model__manufacturer', 'model__device_type',
        )

    def scope(self, user):
        qs = self.get_queryset()
        if not user.is_view_all():
            qs = qs.filter(
                logical__attributes__in=user.get_attributes()
            ).distinct()

        return qs


class Device(models.Model, MigasLink):
    name = models.CharField(
        verbose_name=_('name'),
        max_length=50,
        unique=True,
        db_comment='device name (it may be an organization code)',
    )

    model = models.ForeignKey(
        Model,
        on_delete=models.CASCADE,
        verbose_name=_('model'),
        db_comment='related device model',
    )

    connection = models.ForeignKey(
        Connection,
        on_delete=models.CASCADE,
        verbose_name=_('connection'),
        db_comment='related device connection',
    )

    available_for_attributes = models.ManyToManyField(
        Attribute,
        blank=True,
        verbose_name=_('available for attributes'),
        db_comment='indicates which attributes the device is to publish',
    )

    data = models.TextField(
        verbose_name=_('data'),
        null=True,
        default='{}',
        db_comment='list of fields and values for device connection',
    )

    objects = DeviceManager()

    def location(self):
        data = json.loads(self.data)
        return data.get('LOCATION', '')

    def as_dict(self):
        return {
            'name': self.name,
            'model': self.model.name,
            self.connection.name: json.loads(self.data),
        }

    def total_computers(self, user=None):
        if user and not user.userprofile.is_view_all():
            queryset = self.related_objects('computer', user=user.userprofile)
        else:
            queryset = self.related_objects('computer')

        return queryset.count()

    total_computers.admin_order_field = 'total_computers'
    total_computers.short_description = _('Total computers')

    @staticmethod
    def group_by_connection():
        return Device.objects.values(
            'connection__name',
            'connection__id',
        ).annotate(
            count=models.aggregates.Count('id')
        ).order_by('-count')

    @staticmethod
    def group_by_model():
        return Device.objects.values(
            'model__name',
            'model__id',
        ).annotate(
            count=models.aggregates.Count('id')
        ).order_by('-count')

    @staticmethod
    def group_by_manufacturer():
        return Device.objects.values(
            'model__manufacturer__name',
            'model__manufacturer__id',
        ).annotate(
            count=models.aggregates.Count('id')
        ).order_by('-count')

    def __str__(self):
        return self.name

    def related_objects(self, model, user=None):
        """
        Returns Queryset with the related computers based in logical device attributes
        """
        if model == 'computer':
            from ...client.models import Computer

            if user and not user.userprofile.is_view_all():
                return Computer.productive.scope(user.userprofile).filter(
                    sync_attributes__in=Attribute.objects.filter(logical__device__id=self.id)
                ).distinct()

            else:
                return Computer.productive.filter(
                    sync_attributes__in=Attribute.objects.filter(logical__device__id=self.id)
                ).distinct()

        return None

    def logical_devices_allocated(self):
        return self.logical_set.exclude(attributes=None)

    def incompatible_capabilities(self, target):
        capabilities = []
        for x in self.logical_devices_allocated():
            if target.logical_set.filter(capability=x.capability).count() == 0:
                capabilities.append(str(x.capability))

        for x in target.logical_devices_allocated():
            if self.logical_set.filter(capability=x.capability).count() == 0:
                capabilities.append(str(x.capability))

        return capabilities

    def common_capabilities_allocated(self, target):
        capabilities = []
        for x in self.logical_devices_allocated():
            if target.logical_set.filter(capability=x.capability).count() > 0:
                capabilities.append(x.capability)

        for x in target.logical_devices_allocated():
            if self.logical_set.filter(capability=x.capability).count() > 0:
                if x.capability not in capabilities:
                    capabilities.append(x.capability)

        return capabilities

    @staticmethod
    def replacement(source, target):
        # Moves computers from logical device
        for capability in source.common_capabilities_allocated(target):
            swap_m2m(
                source.logical_set.get(capability=capability),
                target.logical_set.get(capability=capability),
                'attributes'
            )

    def save(self, *args, **kwargs):
        data = json.loads(self.data)
        if 'NAME' in data:
            data['NAME'] = data['NAME'].replace(' ', '_')
            self.data = json.dumps(data)

        super().save(*args, **kwargs)

    class Meta:
        app_label = 'device'
        verbose_name = _('Device')
        verbose_name_plural = _('Devices')
        unique_together = (('connection', 'name'),)
