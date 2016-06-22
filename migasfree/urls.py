# -*- coding: utf-8 -*-

# Copyright (c) 2015-2016 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2016 Alberto Gacías <alberto@migasfree.org>
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

from django.conf.urls import include, url
from django.conf.urls.static import static
from django.conf import settings

from core.routers import router, safe_router as core_safe_router
from client.routers import (
    router as client_router, safe_router as client_safe_router
)
from hardware.routers import (
    router as hardware_router, safe_router as hardware_safe_router
)
from device.routers import router as device_router
from stats.routers import router as stats_router

from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^api/v1/token/', include(router.urls)),
    url(r'^api/v1/token/', include(client_router.urls)),
    url(r'^api/v1/token/', include(stats_router.urls)),
    url(r'^api/v1/token/', include(hardware_router.urls)),
    url(r'^api/v1/token/devices/', include(device_router.urls)),
    url(r'^api/v1/safe/', include(client_safe_router.urls)),
    url(r'^api/v1/safe/', include(core_safe_router.urls)),
    url(r'^api/v1/safe/', include(hardware_safe_router.urls)),
    url(r'^api/v1/', include('migasfree.client.urls')),

    url(r'^token-auth/$', 'rest_framework.authtoken.views.obtain_auth_token'),
    url(r'^token-auth-jwt/', 'rest_framework_jwt.views.obtain_jwt_token'),

    url(r'^docs/', include('rest_framework_swagger.urls')),
    # url(r'^auth/', include('djoser.urls')),
]

if settings.DEBUG and settings.MEDIA_ROOT is not None:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
        show_indexes=True
    )

# initial database setup

from django.core import management
from django.db import connection

from .fixtures import create_initial_data

if not connection.introspection.table_names():
    management.call_command(
        'migrate',
        'auth',
        interactive=False,
        verbosity=1
    )

    management.call_command(
        'migrate',
        interactive=False,
        verbosity=1
    )
    create_initial_data()
