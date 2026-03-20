# Copyright (c) 2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2026 Alberto Gacías <alberto@migasfree.org>
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

import graphene
from graphene_django import DjangoObjectType

from migasfree.device.models import (
    Capability,
    Connection,
    Device,
    Driver,
    Logical,
    Manufacturer,
    Model,
    Type,
)


class CapabilityType(DjangoObjectType):
    class Meta:
        model = Capability
        fields = '__all__'


class ConnectionType(DjangoObjectType):
    class Meta:
        model = Connection
        fields = '__all__'


class DeviceType(DjangoObjectType):
    class Meta:
        model = Device
        fields = '__all__'


class DriverType(DjangoObjectType):
    class Meta:
        model = Driver
        fields = '__all__'


class LogicalDeviceType(DjangoObjectType):
    name = graphene.String()

    class Meta:
        model = Logical
        fields = '__all__'

    def resolve_name(self, info):
        return self.get_name()


class ManufacturerType(DjangoObjectType):
    class Meta:
        model = Manufacturer
        fields = '__all__'


class DeviceModelType(DjangoObjectType):
    class Meta:
        model = Model
        fields = '__all__'


class DeviceTypeType(DjangoObjectType):
    class Meta:
        model = Type
        fields = '__all__'


class Query:
    all_capabilities = graphene.List(CapabilityType)
    capability = graphene.Field(CapabilityType, id=graphene.ID())

    all_connections = graphene.List(ConnectionType)
    connection = graphene.Field(ConnectionType, id=graphene.ID())

    all_devices = graphene.List(DeviceType)
    device = graphene.Field(DeviceType, id=graphene.ID())

    all_drivers = graphene.List(DriverType)
    driver = graphene.Field(DriverType, id=graphene.ID())

    all_logical_devices = graphene.List(LogicalDeviceType)
    logical_device = graphene.Field(LogicalDeviceType, id=graphene.ID())

    all_manufacturers = graphene.List(ManufacturerType)
    manufacturer = graphene.Field(ManufacturerType, id=graphene.ID())

    all_device_models = graphene.List(DeviceModelType)
    device_model = graphene.Field(DeviceModelType, id=graphene.ID())

    all_device_types = graphene.List(DeviceTypeType)
    device_type = graphene.Field(DeviceTypeType, id=graphene.ID())

    def resolve_all_capabilities(self, info, **kwargs):
        return Capability.objects.all()

    def resolve_capability(self, info, id):
        return Capability.objects.get(pk=id)

    def resolve_all_connections(self, info, **kwargs):
        return Connection.objects.select_related('device_type').all()

    def resolve_connection(self, info, id):
        return Connection.objects.select_related('device_type').get(pk=id)

    def resolve_all_devices(self, info, **kwargs):
        return (
            Device.objects.select_related('connection', 'model', 'model__manufacturer')
            .prefetch_related('available_for_attributes')
            .all()
        )

    def resolve_device(self, info, id):
        return (
            Device.objects.select_related('connection', 'model', 'model__manufacturer')
            .prefetch_related('available_for_attributes')
            .get(pk=id)
        )

    def resolve_all_drivers(self, info, **kwargs):
        return Driver.objects.select_related('model', 'model__manufacturer', 'project', 'capability').all()

    def resolve_driver(self, info, id):
        return Driver.objects.select_related('model', 'model__manufacturer', 'project', 'capability').get(pk=id)

    def resolve_all_logical_devices(self, info, **kwargs):
        return (
            Logical.objects.select_related('device', 'capability', 'device__model', 'device__connection')
            .prefetch_related('attributes')
            .all()
        )

    def resolve_logical_device(self, info, id):
        return (
            Logical.objects.select_related('device', 'capability', 'device__model', 'device__connection')
            .prefetch_related('attributes')
            .get(pk=id)
        )

    def resolve_all_manufacturers(self, info, **kwargs):
        return Manufacturer.objects.all()

    def resolve_manufacturer(self, info, id):
        return Manufacturer.objects.get(pk=id)

    def resolve_all_device_models(self, info, **kwargs):
        return Model.objects.select_related('manufacturer', 'device_type').prefetch_related('connections').all()

    def resolve_device_model(self, info, id):
        return Model.objects.select_related('manufacturer', 'device_type').prefetch_related('connections').get(pk=id)

    def resolve_all_device_types(self, info, **kwargs):
        return Type.objects.all()

    def resolve_device_type(self, info, id):
        return Type.objects.get(pk=id)
