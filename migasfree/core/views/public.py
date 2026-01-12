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

import hashlib
import logging
import os
import re
import shutil
import ssl
import tempfile
import time
from mimetypes import guess_type
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import urlcleanup, urlopen, urlretrieve
from wsgiref.util import FileWrapper

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, StreamingHttpResponse
from django.utils.html import escape
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import permissions, status, views
from rest_framework.decorators import action, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from ...client.models import Notification
from ...utils import get_proxied_ip_address
from ..models import ExternalSource, Project
from ..pms import get_available_pms, get_pms

logger = logging.getLogger('migasfree')


def add_notification_get_source_file(error, deployment, resource, remote, from_):
    Notification.objects.create(
        _('Deployment (external source): [%s], resource: [%s], remote file: [%s], from [%s]. Error: %s')
        % (f'{deployment.name}@{deployment.project.name}', resource, remote, from_, error)
    )


def external_downloads(url, local_file):
    temp_file = os.path.join(
        settings.MIGASFREE_PUBLIC_DIR, '.external_downloads', hashlib.md5(local_file.encode('utf-8')).hexdigest()
    )

    if not os.path.exists(temp_file):
        os.makedirs(os.path.dirname(temp_file), exist_ok=True)
        urlcleanup()
        urlretrieve(url, temp_file)
        shutil.move(temp_file, local_file)


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


class RangeFileWrapper:
    # from https://gist.github.com/dcwatson/cb5d8157a8fa5a4a046e

    def __init__(self, file_object, blk_size=8192, offset=0, length=None):
        self.file_object = file_object
        self.file_object.seek(offset, os.SEEK_SET)
        self.remaining = length
        self.blk_size = blk_size

    def close(self):
        if hasattr(self.file_object, 'close'):
            self.file_object.close()

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining is None:
            # If remaining is None, we're reading the entire file
            data = self.file_object.read(self.blk_size)
            if data:
                return data

            raise StopIteration()

        if self.remaining <= 0:
            raise StopIteration()

        data = self.file_object.read(min(self.remaining, self.blk_size))
        if not data:
            raise StopIteration()

        self.remaining -= len(data)

        return data


@permission_classes((permissions.AllowAny,))
@throttle_classes([UserRateThrottle])
class GetSourceFileView(views.APIView):
    serializer_class = None

    async def read_remote_chunks(self, local_file, remote, chunk_size=8192):
        if not remote:
            raise ValueError('Invalid remote file')

        if chunk_size <= 0:
            raise ValueError('Chunk size must be greater than zero')

        try:
            with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp_file:
                while True:
                    data = remote.read(chunk_size)
                    if not data:
                        break

                    yield data
                    tmp_file.write(data)
                    tmp_file.flush()

            try:
                shutil.move(tmp_file.name, local_file)
                tmp_file.close()
            except OSError as e:
                logger.error('Error moving file: %s', str(e))
                os.unlink(tmp_file.name)
                raise
        except Exception as e:
            logger.error('Error reading remote file: %s', str(e))
            raise

    @action(methods=['head'], detail=False)
    def exists(self, request, *args, **kwargs):
        _path = request.get_full_path()
        _local_file = os.path.join(settings.MIGASFREE_PUBLIC_DIR, _path.split('/src/')[1])

        if os.path.getsize(_local_file):
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_404_NOT_FOUND)

    def _parse_path(self, path):
        project_slug = path.split('/')[2]
        source_slug = path.split('/')[4]
        resource = path.split(f'/src/{project_slug}/{settings.MIGASFREE_EXTERNAL_TRAILING_PATH}/{source_slug}/')[1]

        return project_slug, source_slug, resource

    def _handle_file_not_exists(self, source, resource, file_local, path, client_ip):
        if not os.path.exists(os.path.dirname(file_local)):
            os.makedirs(os.path.dirname(file_local))

        if not re.match(r'^[a-zA-Z0-9_\-\+~/.]+$', resource):
            logger.error('Invalid resource path: %s', resource)
            return HttpResponse(f'Invalid resource path: {escape(resource)}', status=status.HTTP_400_BAD_REQUEST)

        url = urljoin(f'{source.base_url}/', resource)
        logger.debug('get url %s', url)

        try:
            remote_file = urlopen(url, context=ssl.SSLContext(ssl.PROTOCOL_SSLv23))

            remote_file_status = remote_file.getcode()
            if remote_file_status != status.HTTP_200_OK:
                add_notification_get_source_file(f'HTTP Error: {remote_file_status}', source, path, url, client_ip)
                return HttpResponse(f'HTTP Error: {remote_file_status} {escape(url)}', status=remote_file_status)

            remote_file_size = remote_file.info().get('Content-Length')
            if remote_file_size is None:
                add_notification_get_source_file('Error: Failed to get file size', source, path, url, client_ip)
                return HttpResponse(
                    f'Error: Failed to get file size {escape(url)}', status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            remote_file_type = remote_file.info().get('Content-Type')

            response = StreamingHttpResponse(self.read_remote_chunks(file_local, remote_file))
            response['Content-Type'] = remote_file_type if remote_file_type else 'application/octet-stream'

            return response
        except HTTPError as e:
            add_notification_get_source_file(f'HTTP Error: {e.code}', source, path, url, client_ip)
            return HttpResponse(f'HTTP Error: {e.code} {escape(url)}', status=e.code)
        except URLError as e:
            add_notification_get_source_file(f'URL Error: {e.reason}', source, path, url, client_ip)
            return HttpResponse(f'URL Error: {escape(e.reason)} {escape(url)}', status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            error_message = f'Error: {e!s} {escape(url)}'
            logger.error(error_message)
            add_notification_get_source_file(f'Error: {e!s}', source, path, url, client_ip)
            return HttpResponse('An internal error has occurred', status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _handle_file_exists(self, file_local, request):
        if not os.path.isfile(file_local):
            return HttpResponse(status=status.HTTP_204_NO_CONTENT)

        size = os.path.getsize(file_local)

        range_header = request.META.get('HTTP_RANGE', '').strip()
        range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)

        range_match = range_re.match(range_header)
        if range_match and os.path.exists(os.path.dirname(file_local)):
            content_type, _ = guess_type(file_local)
            content_type = content_type or 'application/octet-stream'

            first_byte, last_byte = range_match.groups()
            first_byte = int(first_byte) if first_byte else 0

            if first_byte >= size:
                return HttpResponse(status=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE)

            last_byte = int(last_byte) if last_byte else size - 1
            if last_byte >= size:
                last_byte = size - 1

            length = last_byte - first_byte + 1

            logger.debug('get local file streaming %s', file_local)

            with open(file_local, 'rb') as f:
                response = StreamingHttpResponse(
                    RangeFileWrapper(f, offset=first_byte, length=length),
                    status=status.HTTP_206_PARTIAL_CONTENT,
                    content_type=content_type,
                )
                response['Content-Disposition'] = f'attachment; filename={os.path.basename(file_local)}'
                response['Content-Length'] = str(length)
                response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{size}'
                response['Accept-Ranges'] = 'bytes'

                return response

        logger.debug('get local file wrapper %s', file_local)

        with open(file_local, 'rb') as f:
            response = HttpResponse(FileWrapper(f), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename={os.path.basename(file_local)}'
            response['Content-Length'] = size
            response['Accept-Ranges'] = 'bytes'

            return response

    def get(self, request):
        source = None
        path = request.get_full_path()
        project_slug, source_slug, resource = self._parse_path(path)

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
            return self._handle_file_not_exists(source, resource, file_local, path, get_proxied_ip_address(request))

        return self._handle_file_exists(file_local, request)
