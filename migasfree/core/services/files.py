# Copyright (c) 2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2026 Alberto Gacías <alberto@migasfree.org>
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
import tempfile
import ssl
from mimetypes import guess_type
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import urlcleanup, urlopen, urlretrieve
from wsgiref.util import FileWrapper

from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse
from django.utils.html import escape
from django.utils.translation import gettext as _
from rest_framework import status

from ...client.models import Notification
from ...utils import is_safe_url

logger = logging.getLogger('migasfree')


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


class SourceFileService:
    @staticmethod
    async def read_remote_chunks(local_file, remote, chunk_size=8192):
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

    @staticmethod
    def handle_file_not_exists(source, resource, file_local, path, client_ip):
        if not os.path.exists(os.path.dirname(file_local)):
            os.makedirs(os.path.dirname(file_local))

        if not re.match(r'^[a-zA-Z0-9_\-\+~/.]+$', resource):
            logger.error('Invalid resource path: %s', resource)
            return HttpResponse(f'Invalid resource path: {escape(resource)}', status=status.HTTP_400_BAD_REQUEST)

        url = urljoin(f'{source.base_url}/', resource)
        logger.debug('get url %s', url)

        if not is_safe_url(url):
            error_msg = f'Unsafe URL detected: {escape(url)}'
            logger.error(error_msg)
            add_notification_get_source_file(error_msg, source, path, url, client_ip)
            return HttpResponse('Forbidden: Unsafe URL', status=status.HTTP_403_FORBIDDEN)

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

            response = StreamingHttpResponse(SourceFileService.read_remote_chunks(file_local, remote_file))
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

    @staticmethod
    def handle_file_exists(file_local, request):
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
