# -*- coding: utf-8 *-*

# Copyright (c) 2015-2022 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2022 Alberto Gacías <alberto@migasfree.org>
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

import os
import re
import ssl
import time
import shutil
import hashlib

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, StreamingHttpResponse
from mimetypes import guess_type
from rest_framework import status, views, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from urllib.error import URLError, HTTPError
from urllib.request import urlopen, urlretrieve
from wsgiref.util import FileWrapper

from ..pms import get_available_pms, get_pms
from ..models import Project, ExternalSource

import logging
logger = logging.getLogger('migasfree')


def external_downloads(url, local_file):
    temp_file = os.path.join(
        settings.MIGASFREE_PUBLIC_DIR,
        '.external_downloads',
        hashlib.md5(local_file.encode('utf-8')).hexdigest()
    )

    if not os.path.exists(temp_file):
        os.makedirs(os.path.dirname(temp_file), exist_ok=True)
        urlretrieve(url, temp_file)
        shutil.move(temp_file, local_file)


@permission_classes((permissions.AllowAny,))
class PmsView(views.APIView):
    def get(self, request):
        """
        Returns available PMS
        """
        ret = {}

        pms = dict(get_available_pms())
        for key, value in pms.items():
            item = get_pms(key)
            ret[key] = {
                'module': value,
                'mimetype': item.mimetype,
                'extensions': item.extensions
            }

        return Response(ret)


@permission_classes((permissions.AllowAny,))
class ProgrammingLanguagesView(views.APIView):
    def get(self, request):
        """
        Returns available programming languages (to formulas and faults definitions)
        """
        return Response(dict(settings.MIGASFREE_PROGRAMMING_LANGUAGES))


@permission_classes((permissions.AllowAny,))
class ServerInfoView(views.APIView):
    def post(self, request):
        """
        Returns server info
        """
        from ... import __version__, __author__, __contact__, __homepage__

        info = {
            'version': __version__,
            'author': __author__,
            'contact': __contact__,
            'homepage': __homepage__,
        }

        return Response(info)


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
        else:
            if self.remaining <= 0:
                raise StopIteration()

            data = self.file_object.read(min(self.remaining, self.blk_size))
            if not data:
                raise StopIteration()

            self.remaining -= len(data)

            return data


@permission_classes((permissions.AllowAny,))
class GetSourceFileView(views.APIView):
    def read_remote_chunks(local_file, remote, chunk_size=8192):
        _, tmp = tempfile.mkstemp()
        with open(tmp, 'wb') as tmp_file:
            while True:
                data = remote.read(chunk_size)
                if not data:
                    break

                yield data
                tmp_file.write(data)
                tmp_file.flush()

            os.fsync(tmp_file.fileno())

        shutil.move(tmp, local_file)

    @action(methods=['head'], detail=False)
    def exists(self, request, *args, **kwargs):
        _path = request.get_full_path()
        _local_file = os.path.join(settings.MIGASFREE_PUBLIC_DIR, _path.split('/src/')[1])

        if os.path.getsize(_local_file):
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_404_NOT_FOUND)

    def get(self, request):
        source = None

        _path = request.get_full_path()
        project_slug = _path.split('/')[2]
        source_slug = _path.split('/')[4]
        resource = _path.split(
            f'/src/{project_slug}/{settings.MIGASFREE_EXTERNAL_TRAILING_PATH}/{source_slug}/'
        )[1]

        _file_local = os.path.join(settings.MIGASFREE_PUBLIC_DIR, _path.split('/src/')[1])

        try:
            project = Project.objects.get(slug=project_slug)
        except ObjectDoesNotExist:
            return HttpResponse(
                f'Project not exists: {project_slug}',
                status=status.HTTP_404_NOT_FOUND
            )

        if not _file_local.endswith(tuple(project.get_pms().extensions)):  # is a metadata file
            try:
                source = ExternalSource.objects.get(project__slug=project_slug, slug=source_slug)
            except ObjectDoesNotExist:
                return HttpResponse(
                    f'URL not exists: {_path}',
                    status=status.HTTP_404_NOT_FOUND
                )

            if not source.frozen:
                # expired metadata
                if os.path.exists(_file_local) and (
                    source.expire <= 0 or
                    (time.time() - os.stat(_file_local).st_mtime) / (60 * source.expire) > 1
                ):
                    os.remove(_file_local)

        if not os.path.exists(_file_local):
            if not os.path.exists(os.path.dirname(_file_local)):
                os.makedirs(os.path.dirname(_file_local))

            if not source:
                try:
                    source = ExternalSource.objects.get(project__slug=project_slug, slug=source_slug)
                except ObjectDoesNotExist:
                    return HttpResponse(
                        f'URL not exists: {_path}',
                        status=status.HTTP_404_NOT_FOUND
                    )

            url = f'{source.base_url}/{resource}'
            logger.debug('get url %s', url)

            try:
                remote_file = urlopen(url, context=ssl.SSLContext(ssl.PROTOCOL_SSLv23))
                response = StreamingHttpResponse(read_remote_chunks(_file_local, remote_file))
                response['Content-Type'] = 'application/octet-stream'

                return response
            except HTTPError as e:
                return HttpResponse(
                    f'HTTP Error: {e.code} {url}',
                    status=e.code
                )
            except URLError as e:
                return HttpResponse(
                    f'URL Error: {e.reason} {url}',
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            if not os.path.isfile(_file_local):
                return HttpResponse(status=status.HTTP_204_NO_CONTENT)

            range_header = request.META.get('HTTP_RANGE', '').strip()
            range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)
            range_match = range_re.match(range_header)
            if range_match and os.path.exists(os.path.dirname(_file_local)):
                size = os.path.getsize(_file_local)
                content_type, encoding = guess_type(_file_local)
                content_type = content_type or 'application/octet-stream'
                first_byte, last_byte = range_match.groups()
                first_byte = int(first_byte) if first_byte else 0
                last_byte = int(last_byte) if last_byte else size - 1
                if last_byte >= size:
                    last_byte = size - 1
                length = last_byte - first_byte + 1
                response = StreamingHttpResponse(
                    RangeFileWrapper(
                        open(_file_local, 'rb'),
                        offset=first_byte,
                        length=length
                    ),
                    status=status.HTTP_206_PARTIAL_CONTENT,
                    content_type=content_type
                )
                response['Content-Length'] = str(length)
                response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{size}'
                response['Accept-Ranges'] = 'bytes'

                return response

            response = HttpResponse(
                FileWrapper(open(_file_local, 'rb')),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename={os.path.basename(_file_local)}'
            response['Content-Length'] = os.path.getsize(_file_local)

            return response
