# Copyright (c) 2015-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2026 Alberto Gacías <alberto@migasfree.org>
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

import logging
import os
import time

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.utils.html import escape
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import permissions, status, views
from rest_framework.decorators import action, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from ...utils import get_proxied_ip_address
from ..models import ExternalSource, Project
from ..pms import get_available_pms, get_pms
from ..services.files import SourceFileService

logger = logging.getLogger('migasfree')


@permission_classes((permissions.AllowAny,))
@throttle_classes([UserRateThrottle])
class PmsView(views.APIView):
    @extend_schema(
        description='Returns available PMS',
        responses={
            status.HTTP_200_OK: {
                'type': 'object',
                'properties': {
                    'pms': {
                        'type': 'object',
                        'properties': {
                            'module': {'type': 'string'},
                            'mimetype': {'type': 'array', 'items': {'type': 'string'}},
                            'extensions': {'type': 'array', 'items': {'type': 'string'}},
                            'architectures': {'type': 'array', 'items': {'type': 'string'}},
                        },
                    }
                },
            }
        },
        tags=['public'],
    )
    def get(self, request):
        ret = {}

        for key, value in dict(get_available_pms()).items():
            item = get_pms(key)
            ret[key] = {
                'module': value,
                'mimetype': item.mimetype,
                'extensions': item.extensions,
                'architectures': item.architectures,
            }

        return Response(ret)


@permission_classes((permissions.AllowAny,))
@throttle_classes([UserRateThrottle])
class ProgrammingLanguagesView(views.APIView):
    @extend_schema(
        description='Returns available programming languages (to formulas and faults definitions)',
        responses={status.HTTP_200_OK: dict(settings.MIGASFREE_PROGRAMMING_LANGUAGES)},
        examples=[
            OpenApiExample(
                name='successfully response',
                value=dict(settings.MIGASFREE_PROGRAMMING_LANGUAGES),
                response_only=True,
            ),
        ],
        tags=['public'],
    )
    def get(self, request):
        return Response(dict(settings.MIGASFREE_PROGRAMMING_LANGUAGES))


@extend_schema(
    methods=['GET', 'POST'],
    description='Returns server info',
    responses={
        status.HTTP_200_OK: {
            'type': 'object',
            'properties': {
                'version': {'type': 'string'},
                'author': {'type': 'array', 'items': {'type': 'string'}},
                'contact': {'type': 'string'},
                'homepage': {'type': 'string'},
                'organization': {'type': 'string'},
            },
        }
    },
    tags=['public'],
)
@permission_classes((permissions.AllowAny,))
@throttle_classes([UserRateThrottle])
class ServerInfoView(views.APIView):
    serializer_class = None

    def get(self, request):
        from ... import __author__, __contact__, __homepage__, __version__

        info = {
            'version': __version__,
            'author': __author__,
            'contact': __contact__,
            'homepage': __homepage__,
            'organization': settings.MIGASFREE_ORGANIZATION,
        }

        return Response(info)

    def post(self, request):
        """
        Compatibility with older clients
        """
        return self.get(request)


@permission_classes((permissions.AllowAny,))
@throttle_classes([UserRateThrottle])
class GetSourceFileView(views.APIView):
    serializer_class = None

    @action(methods=['head'], detail=False)
    def exists(self, request, *args, **kwargs):
        _path = request.get_full_path()
        _local_file = os.path.join(settings.MIGASFREE_PUBLIC_DIR, _path.split('/src/')[1])

        if os.path.getsize(_local_file):
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_404_NOT_FOUND)

    def get(self, request):
        path = request.get_full_path()
        project_slug = path.split('/')[2]
        source_slug = path.split('/')[4]
        resource = path.split(f'/src/{project_slug}/{settings.MIGASFREE_EXTERNAL_TRAILING_PATH}/{source_slug}/')[1]

        try:
            project = Project.objects.get(slug=project_slug)
        except ObjectDoesNotExist:
            return HttpResponse(f'Project not exists: {escape(project_slug)}', status=status.HTTP_404_NOT_FOUND)

        try:
            source = ExternalSource.objects.get(project__slug=project_slug, slug=source_slug)
        except ObjectDoesNotExist:
            return HttpResponse(f'URL not exists: {escape(path)}', status=status.HTTP_404_NOT_FOUND)

        file_local = os.path.normpath(os.path.join(settings.MIGASFREE_PUBLIC_DIR, path.split('/src/')[1]))
        if not file_local.startswith(settings.MIGASFREE_PUBLIC_DIR):
            return HttpResponse('Invalid file path', status=status.HTTP_400_BAD_REQUEST)

        if (
            not file_local.endswith(tuple(project.get_pms().extensions))
            and not source.frozen
            and os.path.exists(file_local)
            and (source.expire <= 0 or time.time() - os.path.getmtime(file_local) > source.expire * 60)
        ):
            os.remove(file_local)  # expired metadata

        if not os.path.exists(file_local) or os.path.getsize(file_local) == 0:
            return SourceFileService.handle_file_not_exists(
                source, resource, file_local, path, get_proxied_ip_address(request)
            )

        return SourceFileService.handle_file_exists(file_local, request)
