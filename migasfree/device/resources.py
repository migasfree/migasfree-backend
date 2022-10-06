# -*- coding: utf-8 -*-

# Copyright (c) 2022 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2022 Alberto Gacías <alberto@migasfree.org>
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

from import_export import resources, fields

from .models import (
    Connection, Device, Driver,
    Capability, Logical, Manufacturer,
    Model, Type
)


class CapabilityResource(resources.ModelResource):
    class Meta:
        model = Capability


class ConnectionResource(resources.ModelResource):
    class Meta:
        model = Connection


class DeviceResource(resources.ModelResource):
    computers = fields.Field()

    class Meta:
        model = Device
        export_order = (
            'id', 'name', 'model', 'connection',
            'available_for_attributes', 'data', 'computers'
        )

    def dehydrate_computers(self, obj):
        return obj.total_computers()


class LogicalResource(resources.ModelResource):
    class Meta:
        model = Logical
        fields = (
            'id', 'device', 'device__name',
            'capability', 'capability__name', 'alternative_capability_name',
            'attributes'
        )
        export_order = (
            'id', 'device', 'device__name',
            'capability', 'capability__name', 'alternative_capability_name',
            'attributes'
        )


class ManufacturerResource(resources.ModelResource):
    class Meta:
        model = Manufacturer


class ModelResource(resources.ModelResource):
    class Meta:
        model = Model
        fields = (
            'id', 'name', 'manufacturer', 'manufacturer__name',
            'device_type', 'device_type__name', 'connections'
        )
        export_order = (
            'id', 'name', 'manufacturer', 'manufacturer__name',
            'device_type', 'device_type__name', 'connections'
        )


class TypeResource(resources.ModelResource):
    class Meta:
        model = Type
