# -*- coding: UTF-8 -*-

# Copyright (c) 2020 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2020 Alberto Gacías <alberto@migasfree.org>
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

from rest_framework.response import Response
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import permission_classes
from django_redis import get_redis_connection

from ...utils import decode_dict


@permission_classes((permissions.IsAuthenticated,))
class AlertsViewSet(viewsets.ViewSet):
    def list(self, request, format=None):
        con = get_redis_connection()

        response = [
            decode_dict(con.hgetall('migasfree:chk:repos')),
            decode_dict(con.hgetall('migasfree:chk:syncs')),
            decode_dict(con.hgetall('migasfree:chk:active_deploys')),
            decode_dict(con.hgetall('migasfree:chk:orphan')),
            decode_dict(con.hgetall('migasfree:chk:notifications')),
            decode_dict(con.hgetall('migasfree:chk:delayed')),
            decode_dict(con.hgetall('migasfree:chk:finished_deploys')),
            decode_dict(con.hgetall('migasfree:chk:faults')),
            decode_dict(con.hgetall('migasfree:chk:errors')),
        ]

        return Response(response, status=status.HTTP_200_OK)
