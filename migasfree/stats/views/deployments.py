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

from collections import defaultdict

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django_redis import get_redis_connection

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...core.models import Deployment, Project


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

    @action(methods=['get'], detail=False, url_path='enabled/project')
    def enabled_by_project(self, request, format=None):
        total = Deployment.objects.scope(request.user.userprofile).filter(enabled=True).count()

        values_null = defaultdict(list)
        for item in Deployment.objects.scope(
            request.user.userprofile
        ).filter(
            enabled=True, schedule=None
        ).values(
            'project__id',
        ).annotate(
            count=Count('id')
        ).order_by('project__id', '-count'):
            values_null[item.get('project__id')].append(
                {
                    'name': _('Without schedule'),
                    'value': item.get('count'),
                    'project_id': item.get('project__id'),
                    # FIXME 'schedule': null
                }
            )

        values_not_null = defaultdict(list)
        for item in Deployment.objects.scope(
            request.user.userprofile
        ).filter(
            enabled=True,
        ).filter(
            ~Q(schedule=None)
        ).values(
            'project__id',
        ).annotate(
            count=Count('id')
        ).order_by('project__id', '-count'):
            values_not_null[item.get('project__id')].append(
                {
                    'name': _('With schedule'),
                    'value': item.get('count'),
                    'project_id': item.get('project__id'),
                    # FIXME 'schedule': true
                }
            )

        data = []
        for project in Project.objects.scope(request.user.userprofile).all():
            count = 0
            data_project = []
            if project.id in values_null:
                count += values_null[project.id][0]['value']
                data_project.append(values_null[project.id][0])
            if project.id in values_not_null:
                count += values_not_null[project.id][0]['value']
                data_project.append(values_not_null[project.id][0])
            if count:
                data.append(
                    {
                        'name': project.name,
                        'value': count,
                        'project_id': project.id,
                        'data': data_project
                    }
                )

        return Response(
            {
                'title': _('Enabled Deployments'),
                'total': total,
                'data': data,
            },
            status=status.HTTP_200_OK
        )
