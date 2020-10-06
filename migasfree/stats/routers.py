# -*- coding: utf-8 *-*

# Copyright (c) 2015-2020 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2020 Alberto Gacías <alberto@migasfree.org>
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

from rest_framework import routers

from . import views

router = routers.DefaultRouter()

router.register(r'stats/syncs', views.SyncStatsViewSet, basename='stats-syncs')
router.register(
    r'stats/computers', views.ComputerStatsViewSet, basename='stats-computers'
)
router.register(
    r'stats/deployments',
    views.DeploymentStatsViewSet,
    basename='stats-deployments'
)
router.register(
    r'stats/features',
    views.ClientAttributeStatsViewSet,
    basename='stats-features'
)
router.register(
    r'stats/tags',
    views.ServerAttributeStatsViewSet,
    basename='stats-tags'
)
router.register(
    r'stats/devices',
    views.DeviceStatsViewSet,
    basename='stats-devices'
)
router.register(
    r'stats/migrations',
    views.MigrationStatsViewSet,
    basename='stats-migrations'
)
router.register(
    r'stats/status-logs',
    views.StatusLogStatsViewSet,
    basename='stats-status-logs'
)
router.register(
    r'stats/notifications',
    views.NotificationStatsViewSet,
    basename='stats-notifications'
)
router.register(
    r'stats/errors',
    views.ErrorStatsViewSet,
    basename='stats-errors'
)
router.register(
    r'stats/faults',
    views.FaultStatsViewSet,
    basename='stats-faults'
)
router.register(
    r'stats/stores',
    views.StoreStatsViewSet,
    basename='stats-stores'
)
