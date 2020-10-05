# -*- coding: UTF-8 -*-

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

from django.shortcuts import get_object_or_404
from django_redis import get_redis_connection

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...core.models import Deployment


@permission_classes((permissions.IsAuthenticated,))
class DeploymentStatsViewSet(viewsets.ViewSet):
    @action(methods=['get'], detail=True, url_path='computers/assigned')
    def assigned_computers(self, request, pk=None):
        deploy = get_object_or_404(Deployment, pk=pk)

        con = get_redis_connection()
        response = con.smembers(
            'migasfree:deployments:%d:computers' % deploy.id
        )

        return Response(
            list(response),
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True, url_path='computers/status/ok')
    def computers_with_ok_status(self, request, pk=None):
        deploy = get_object_or_404(Deployment, pk=pk)

        con = get_redis_connection()
        response = con.smembers('migasfree:deployments:%d:ok' % deploy.id)

        return Response(
            list(response),
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True, url_path='computers/status/error')
    def computers_with_error_status(self, request, pk=None):
        deploy = get_object_or_404(Deployment, pk=pk)

        con = get_redis_connection()
        response = con.smembers('migasfree:deployments:%d:error' % deploy.id)

        return Response(
            list(response),
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True)
    def timeline(self, request, pk=None):
        deploy = get_object_or_404(Deployment, pk=pk)

        con = get_redis_connection()

        response = {
            'computers': {
                'assigned': con.scard(
                    'migasfree:deployments:%d:computers' % deploy.id
                ),
                'ok': con.scard('migasfree:deployments:%d:ok' % deploy.id),
                'error': con.scard('migasfree:deployments:%d:error' % deploy.id)
            },
            'schedule': deploy.schedule_timeline()
        }

        return Response(
            response,
            status=status.HTTP_200_OK
        )
