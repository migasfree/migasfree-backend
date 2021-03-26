# -*- coding: utf-8 -*-

# Copyright (c) 2015-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2021 Alberto Gacías <alberto@migasfree.org>
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
from django.urls import path, re_path
from graphene_django.views import GraphQLView
from rest_framework import permissions, routers
from rest_framework.authtoken import views
from rest_framework.documentation import include_docs_urls
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
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

from .api_v4.views import (
    api_v4, computer_label, ServerInfoView,
    get_key_repositories, get_computer_info,
)

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
    re_path(r'^grappelli/', include('grappelli.urls')),
    re_path(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^markdownx/', include('markdownx.urls')),

    re_path(r'^api/v1/token/', include(token_router.urls)),
    re_path(r'^api/v1/token/devices/', include(device_router.urls)),
    re_path(r'^api/v1/token/catalog/', include(catalog_router.urls)),
    re_path(r'^api/v1/safe/', include(safe_router.urls)),
    re_path(r'^api/v1/', include('migasfree.core.urls')),
    re_path(r'^api/v1/', include('migasfree.client.urls')),

    re_path(r'^token-auth/$', views.obtain_auth_token),
    path('token-auth-jwt/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token-refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    re_path(r'^rest-auth/', include('dj_rest_auth.urls')),

    re_path(r'^api/$', api_v4, name='api_v4'),
    re_path(
        r'^computer/(?P<uuid>.+)/label/$',
        computer_label,
        name='computer_label',
    ),
    re_path(
        r'^get_key_repositories/$',
        get_key_repositories,
        name='get_key_repositories'
    ),
    re_path(
        r'^get_computer_info/$',
        get_computer_info,
        name='get_computer_info'
    ),
    re_path(r'^api/v1/public/server/info/', ServerInfoView.as_view()),

    re_path(r'^', include('django.contrib.auth.urls')),
    re_path(r'^api-docs/', include_docs_urls(title=TITLE)),
    # re_path(r'^auth/', include('djoser.urls')),

    re_path(r'^docs(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^docs/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('graphql', GraphQLView.as_view(graphiql=True)),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
        re_path(r'^silk/', include('silk.urls', namespace='silk')),
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
