# -*- coding: utf-8 -*-

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

from django.conf.urls import include, url
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path
from graphene_django.views import GraphQLView
from rest_framework import permissions
from rest_framework.authtoken import views
from rest_framework.schemas import get_schema_view
from rest_framework.documentation import include_docs_urls
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .core.routers import router, safe_router as core_safe_router
from .client.routers import (
    router as client_router, safe_router as client_safe_router
)
from .hardware.routers import (
    router as hardware_router, safe_router as hardware_safe_router
)
from .device.routers import router as device_router
from .stats.routers import router as stats_router
from .app_catalog.routers import router as catalog_router

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from django.contrib import admin
admin.autodiscover()

admin.site.site_header = 'Migasfree Backend Admin'
admin.site.site_title = 'Migasfree Backend Admin Portal'
admin.site.index_title = 'Welcome to Migasfree Backend Portal'

TITLE = 'Migasfree REST API'

schema_view = get_schema_view(
   openapi.Info(
      title=TITLE,
      default_version='v1',
      # description='Test description',
      # terms_of_service='https://www.google.com/policies/terms/',
      contact=openapi.Contact(email='fun.with@migasfree.org'),
      license=openapi.License(name='GPLv3'),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^markdownx/', include('markdownx.urls')),

    url(r'^api/v1/token/', include(router.urls)),
    url(r'^api/v1/token/', include(client_router.urls)),
    url(r'^api/v1/token/', include(stats_router.urls)),
    url(r'^api/v1/token/', include(hardware_router.urls)),
    url(r'^api/v1/token/devices/', include(device_router.urls)),
    url(r'^api/v1/token/catalog/', include(catalog_router.urls)),
    url(r'^api/v1/safe/', include(client_safe_router.urls)),
    url(r'^api/v1/safe/', include(core_safe_router.urls)),
    url(r'^api/v1/safe/', include(hardware_safe_router.urls)),
    url(r'^api/v1/', include('migasfree.core.urls')),
    url(r'^api/v1/', include('migasfree.client.urls')),

    url(r'^token-auth/$', views.obtain_auth_token),
    path('token-auth-jwt/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token-refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    url(r'^rest-auth/', include('rest_auth.urls')),

    url(r'^', include('django.contrib.auth.urls')),
    url(r'^api-docs/', include_docs_urls(title=TITLE)),
    # url(r'^auth/', include('djoser.urls')),

    url(r'^docs(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^docs/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('graphql', GraphQLView.as_view(graphiql=True)),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

    if settings.MEDIA_ROOT is not None:
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
