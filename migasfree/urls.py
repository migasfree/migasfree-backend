# -*- coding: utf-8 -*-

# Copyright (c) 2015-2024 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2024 Alberto Gacías <alberto@migasfree.org>
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

from django.conf.urls import include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.core import management
from django.db import connection
from django.db.utils import OperationalError
from django.urls import path, re_path, reverse_lazy
from django.views.generic.base import RedirectView
from graphene_django.views import GraphQLView
from rest_framework import routers
from rest_framework.authtoken import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    # SpectacularRedocView,
    SpectacularSwaggerView,
)

from .core.routers import router as core_router, safe_router as core_safe_router
from .client.routers import (
    router as client_router, safe_router as client_safe_router
)
from .hardware.routers import (
    router as hardware_router, safe_router as hardware_safe_router
)
from .device.routers import router as device_router
from .stats.routers import router as stats_router
from .app_catalog.routers import router as catalog_router
from .core.views import GetSourceFileView
from .fixtures import create_initial_data

admin.autodiscover()

admin.site.site_header = 'Migasfree Backend Admin'
admin.site.site_title = 'Migasfree Backend Admin Portal'
admin.site.index_title = 'Welcome to Migasfree Backend Portal'

token_router = routers.DefaultRouter()
token_router.registry.extend(core_router.registry)
token_router.registry.extend(client_router.registry)
token_router.registry.extend(stats_router.registry)
token_router.registry.extend(hardware_router.registry)

safe_router = routers.DefaultRouter()
safe_router.registry.extend(core_safe_router.registry)
safe_router.registry.extend(client_safe_router.registry)
safe_router.registry.extend(hardware_safe_router.registry)

urlpatterns = [
    re_path(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^markdownx/', include('markdownx.urls')),

    re_path(r'^api/v1/token/', include(token_router.urls)),
    re_path(r'^api/v1/token/devices/', include(device_router.urls)),
    re_path(r'^api/v1/token/catalog/', include(catalog_router.urls)),
    re_path(r'^api/v1/safe/', include(safe_router.urls)),
    re_path(r'^api/v1/', include('migasfree.core.urls')),
    re_path(r'^api/v1/', include('migasfree.client.urls')),

    re_path(r'^src/', GetSourceFileView.as_view()),

    re_path(r'^token-auth/$', views.obtain_auth_token),
    path('token-auth-jwt/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token-refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    re_path(r'^rest-auth/', include('dj_rest_auth.urls')),

    re_path(r'^', include('django.contrib.auth.urls')),
    # re_path(r'^auth/', include('djoser.urls')),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    re_path(r'^docs/$', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # re_path(r'^redoc/$', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('graphql', GraphQLView.as_view(graphiql=True)),

    path('', include('migasfree.api_v4.urls')),
    path('', RedirectView.as_view(url=reverse_lazy('admin:index'))),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
        # re_path(r'^silk/', include('silk.urls', namespace='silk')),
    ]

    if settings.MEDIA_ROOT is not None:
        urlpatterns += static(
            settings.MEDIA_URL,
            document_root=settings.MEDIA_ROOT,
            show_indexes=True
        )

# initial database setup
try:
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
except OperationalError as e:
    print(e)
