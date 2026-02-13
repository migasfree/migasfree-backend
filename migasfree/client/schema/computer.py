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

from migasfree.client.models import Computer
from migasfree.core.schema import AttributeType
from migasfree.hardware.models import Node
from migasfree.hardware.schema import HardwareNodeType

from .device import LogicalDeviceType
from .error import ErrorType
from .fault import FaultType
from .software import PackageHistoryType


class ComputerType(DjangoObjectType):
    devices = graphene.List(LogicalDeviceType)
    software_history = graphene.List(PackageHistoryType)
    faults = graphene.List(FaultType)
    errors = graphene.List(ErrorType)
    attributes = graphene.List(AttributeType)
    tags = graphene.List(AttributeType)
    hardware = graphene.Field(HardwareNodeType)

    class Meta:
        model = Computer
        fields = '__all__'

    def resolve_devices(self, info):
        return self.logical_devices()

    def resolve_software_history(self, info):
        return self.packagehistory_set.all()

    def resolve_faults(self, info):
        return self.fault_set.all()

    def resolve_errors(self, info):
        return self.error_set.all()

    def resolve_attributes(self, info):
        return self.sync_attributes.all()

    def resolve_tags(self, info):
        return self.tags.all()

    def resolve_hardware(self, info):
        return Node.objects.filter(computer=self, parent=None).first()
