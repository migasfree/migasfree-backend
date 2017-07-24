# -*- coding: utf-8 *-*

# Copyright (c) 2015-2017 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2017 Alberto Gacías <alberto@migasfree.org>
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

router.register(r'computers', views.ComputerViewSet)
router.register(r'errors', views.ErrorViewSet)
router.register(r'faults-definitions', views.FaultDefinitionViewSet)
router.register(r'faults', views.FaultViewSet)
router.register(r'notifications', views.NotificationViewSet)
router.register(r'computers-packages', views.PackageHistoryViewSet)
router.register(r'migrations', views.MigrationViewSet)
router.register(r'status-logs', views.StatusLogViewSet)
router.register(r'syncs', views.SynchronizationViewSet)

safe_router = routers.DefaultRouter()

safe_router.register(
    r'computers',
    views.SafeComputerViewSet,
    base_name='computers'
)
