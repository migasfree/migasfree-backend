# -*- coding: utf-8 -*-

# Copyright (c) 2020-2024 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2020-2024 Alberto Gacías <alberto@migasfree.org>
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

from .alerts import AlertsViewSet
from .applications import ApplicationStatsViewSet
from .attributes import ClientAttributeStatsViewSet, ServerAttributeStatsViewSet
from .computers import ComputerStatsViewSet
from .deployments import DeploymentStatsViewSet
from .devices import DeviceStatsViewSet
from .errors import ErrorStatsViewSet
from .faults import FaultStatsViewSet
from .migrations import MigrationStatsViewSet
from .notifications import NotificationStatsViewSet
from .packages_history import PackageHistoryStatsViewSet
from .packages import PackageStatsViewSet
from .status_logs import StatusLogStatsViewSet
from .stores import StoreStatsViewSet
from .syncs import SyncStatsViewSet

__all__ = [
    'AlertsViewSet',
    'ApplicationStatsViewSet',
    'ClientAttributeStatsViewSet', 'ServerAttributeStatsViewSet',
    'ComputerStatsViewSet',
    'DeploymentStatsViewSet',
    'DeviceStatsViewSet',
    'ErrorStatsViewSet',
    'FaultStatsViewSet',
    'MigrationStatsViewSet',
    'NotificationStatsViewSet',
    'PackageHistoryStatsViewSet',
    'PackageStatsViewSet',
    'StatusLogStatsViewSet',
    'StoreStatsViewSet',
    'SyncStatsViewSet',
]
