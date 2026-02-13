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

from migasfree.hardware.models import (
    Capability,
    Configuration,
    LogicalName,
    Node,
)


class HardwareCapabilityType(DjangoObjectType):
    class Meta:
        model = Capability
        fields = '__all__'


class HardwareConfigurationType(DjangoObjectType):
    class Meta:
        model = Configuration
        fields = '__all__'


class HardwareLogicalNameType(DjangoObjectType):
    class Meta:
        model = LogicalName
        fields = '__all__'


class HardwareNodeType(DjangoObjectType):
    children = graphene.List(lambda: HardwareNodeType)
    capabilities = graphene.List(HardwareCapabilityType)
    configurations = graphene.List(HardwareConfigurationType)
    logical_names = graphene.List(HardwareLogicalNameType)

    class Meta:
        model = Node
        fields = '__all__'

    def resolve_children(self, info):
        return self.child.all()

    def resolve_capabilities(self, info):
        return self.capability_set.all()

    def resolve_configurations(self, info):
        return self.configuration_set.all()

    def resolve_logical_names(self, info):
        return self.logicalname_set.all()
