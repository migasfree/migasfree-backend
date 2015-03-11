# -*- coding: utf-8 *-*

# Copyright (c) 2015 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015 Alberto Gacías <alberto@migasfree.org>
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

router.register(r'platforms', views.PlatformViewSet)
router.register(r'projects', views.ProjectViewSet)
router.register(r'stores', views.StoreViewSet)
router.register(r'stamps', views.ServerPropertyViewSet)
router.register(r'formulas', views.ClientPropertyViewSet)
router.register(r'tags', views.ServerAttributeViewSet)
router.register(r'features', views.ClientAttributeViewSet)
router.register(r'schedules', views.ScheduleViewSet)
router.register(r'packages', views.PackageViewSet)
router.register(r'repos', views.RepositoryViewSet)
#router.register(r'auth', views.AuthViewSet, base_name='auth')
#router.register(r'accounts', views.UserViewSet)
#router.register(r'account-groups', views.GroupViewSet)

safe_router = routers.DefaultRouter()

safe_router.register(
    r'packages',
    views.SafePackageViewSet,
    base_name='safe_packages'
)
