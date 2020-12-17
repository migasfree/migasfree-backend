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

router.register(r'platforms', views.PlatformViewSet)
router.register(r'projects', views.ProjectViewSet)
router.register(r'stores', views.StoreViewSet)
router.register(r'attribute-sets', views.AttributeSetViewSet)
router.register(r'attributes', views.AttributeViewSet)
router.register(r'stamps', views.ServerPropertyViewSet)
router.register(r'properties', views.PropertyViewSet)
router.register(r'formulas', views.ClientPropertyViewSet)
router.register(r'tags', views.ServerAttributeViewSet)
router.register(r'features', views.ClientAttributeViewSet)
router.register(r'schedules', views.ScheduleViewSet)
router.register(r'packages', views.PackageViewSet)
router.register(r'deployments/internal-sources', views.InternalSourceViewSet)
router.register(r'deployments/external-sources', views.ExternalSourceViewSet)
router.register(r'deployments', views.DeploymentViewSet)
router.register(r'domains', views.DomainViewSet)
router.register(r'scopes', views.ScopeViewSet)
router.register(r'user-profiles', views.UserProfileViewSet)
# router.register(r'auth', views.AuthViewSet, basename='auth')
# router.register(r'accounts', views.UserViewSet)
router.register(r'accounts/groups', views.GroupViewSet)
router.register(r'accounts/permissions', views.PermissionViewSet)

safe_router = routers.DefaultRouter()

safe_router.register(
    r'packages',
    views.SafePackageViewSet,
    basename='safe_packages'
)
