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

from .computer import ComputerType
from .device import (
    ConnectionType,
    DeviceModelType,
    DeviceType,
    DeviceTypeType,
    LogicalDeviceType,
    ManufacturerType,
)
from .error import ErrorType
from .fault import FaultType
from .query import Query
from .software import PackageHistoryType, PackageType

__all__ = [
    'ComputerType',
    'ConnectionType',
    'DeviceModelType',
    'DeviceType',
    'DeviceTypeType',
    'ErrorType',
    'FaultType',
    'LogicalDeviceType',
    'ManufacturerType',
    'PackageHistoryType',
    'PackageType',
    'Query',
]
