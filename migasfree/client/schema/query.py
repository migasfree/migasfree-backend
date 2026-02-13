# Copyright (c) 2019-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2019-2026 Alberto Gacías <alberto@migasfree.org>
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

from migasfree.client.models import Computer, Error, FaultDefinition
from migasfree.core.models import Package
from migasfree.device.models import (
    Device,
    Manufacturer,
    Model,
    Type,
)

from .computer import ComputerType
from .device import (
    DeviceModelType,
    DeviceType,
    DeviceTypeType,
    ManufacturerType,
)
from .error import ErrorType
from .fault import FaultDefinitionType
from .software import PackageType


class Query:
    all_computers = graphene.List(ComputerType)
    all_errors = graphene.List(ErrorType)
    computer = graphene.Field(ComputerType, id=graphene.ID())

    all_manufacturers = graphene.List(ManufacturerType)
    all_device_models = graphene.List(DeviceModelType)
    all_device_types = graphene.List(DeviceTypeType)
    all_devices = graphene.List(DeviceType)
    all_packages = graphene.List(PackageType)
    all_fault_definitions = graphene.List(FaultDefinitionType)

    def resolve_all_computers(self, info, **kwargs):
        return Computer.objects.all()

    def resolve_all_errors(self, info, **kwargs):
        return Error.objects.select_related('computer').all()

    def resolve_computer(self, info, id):
        return Computer.objects.get(pk=id)

    def resolve_all_manufacturers(self, info, **kwargs):
        return Manufacturer.objects.all()

    def resolve_all_device_models(self, info, **kwargs):
        return Model.objects.select_related('manufacturer', 'device_type').all()

    def resolve_all_device_types(self, info, **kwargs):
        return Type.objects.all()

    def resolve_all_devices(self, info, **kwargs):
        return Device.objects.select_related('model__manufacturer', 'model__device_type', 'connection').all()

    def resolve_all_packages(self, info, **kwargs):
        return Package.objects.all()

    def resolve_all_fault_definitions(self, info, **kwargs):
        return FaultDefinition.objects.all()
