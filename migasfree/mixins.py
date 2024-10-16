# -*- coding: UTF-8 -*-

# Copyright (c) 2022-2024 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2022-2024 Alberto Gacías <alberto@migasfree.org>
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

from django.db import connections
from django.db.utils import OperationalError

from rest_framework import status, viewsets
from rest_framework.response import Response

logger = logging.getLogger('migasfree')


class DatabaseCheckMixin(viewsets.ViewSet):
    def dispatch(self, request, *args, **kwargs):
        try:
            connections['default'].cursor()
            return super().dispatch(request, *args, **kwargs)
        except OperationalError as e:
            logger.error('Operational error in database: %s', e)
            response = Response(
                'Operational error in database',
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            if not getattr(request, 'accepted_renderer', None):
                neg = self.perform_content_negotiation(request, force=True)
                request.accepted_renderer, request.accepted_media_type = neg

            response.accepted_renderer = request.accepted_renderer
            response.accepted_media_type = request.accepted_media_type
            response.renderer_context = self.get_renderer_context()

            return response
