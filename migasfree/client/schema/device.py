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
    Connection,
    Device,
    Logical,
    Manufacturer,
    Model,
    Type,
)


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


class ConnectionType(DjangoObjectType):
    class Meta:
        model = Connection
        fields = '__all__'


class DeviceType(DjangoObjectType):
    class Meta:
        model = Device
        fields = '__all__'


class LogicalDeviceType(DjangoObjectType):
    name = graphene.String()

    class Meta:
        model = Logical
        fields = '__all__'

    def resolve_name(self, info):
        return self.get_name()
