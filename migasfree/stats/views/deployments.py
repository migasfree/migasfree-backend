# -*- coding: UTF-8 -*-

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

from collections import defaultdict
from datetime import timedelta, datetime

from django.db.models import Q
from django.db.models.aggregates import Count
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django_redis import get_redis_connection

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...client.models import Computer
from ...core.models import Deployment, Project, ScheduleDelay
from ...utils import time_horizon


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
            list(map(int, response)),
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True, url_path='computers/status/ok')
    def computers_with_ok_status(self, request, pk=None):
        deploy = get_object_or_404(Deployment, pk=pk)

        con = get_redis_connection()
        response = con.smembers('migasfree:deployments:%d:ok' % deploy.id)

        return Response(
            list(map(int, response)),
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True, url_path='computers/status/error')
    def computers_with_error_status(self, request, pk=None):
        deploy = get_object_or_404(Deployment, pk=pk)

        con = get_redis_connection()
        response = con.smembers('migasfree:deployments:%d:error' % deploy.id)

        return Response(
            list(map(int, response)),
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

    @action(methods=['get'], detail=True, url_path='computers/delay')
    def provided_computers_by_delay(self, request, pk=None):
        deploy = get_object_or_404(Deployment, pk=pk)
        if not deploy.schedule:
            return Response(
                {
                    'detail': _('This deployment has not schedule'),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        rolling_date = deploy.start_date

        available_data = []
        provided_data = []
        labels = []
        chart_data = {}

        if deploy.domain:
            q_in_domain = ~Q(sync_attributes__id__in=deploy.domain.included_attributes.all())
            q_ex_domain = Q(sync_attributes__id__in=deploy.domain.excluded_attributes.all())
        else:
            q_in_domain = Q()
            q_ex_domain = Q()

        lst_attributes = list(deploy.included_attributes.values_list('id', flat=True))
        value = Computer.productive.scope(request.user.userprofile).filter(
            Q(sync_attributes__id__in=lst_attributes) &
            Q(project__id=deploy.project.id)
        ).exclude(
            Q(sync_attributes__id__in=deploy.excluded_attributes.all())
        ).exclude(
            q_in_domain
        ).exclude(
            q_ex_domain
        ).values('id').distinct().count()

        date_format = '%Y-%m-%d'
        now = datetime.now()

        delays = ScheduleDelay.objects.filter(
            schedule__id=deploy.schedule.id
        ).order_by('delay')
        len_delays = len(delays)

        for i, item in enumerate(delays):
            lst_att_delay = list(item.attributes.values_list('id', flat=True))

            start_horizon = datetime.strptime(
                str(time_horizon(rolling_date, 0)),
                date_format
            )
            if i < (len_delays - 1):
                end_horizon = datetime.strptime(
                    str(time_horizon(rolling_date, delays[i + 1].delay - item.delay)),
                    date_format
                )
            else:
                end_horizon = datetime.strptime(
                    str(time_horizon(rolling_date, item.duration)),
                    date_format
                )

            duration = 0
            for real_days in range(0, (end_horizon - start_horizon).days):
                loop_date = start_horizon + timedelta(days=real_days)
                weekday = int(loop_date.strftime("%w"))  # [0(Sunday), 6]
                if weekday not in [0, 6]:
                    value += Computer.productive.scope(request.user.userprofile).extra(
                        select={'deployment': 'id'},
                        where=[
                            'computer_id %% {} = {}'.format(item.duration, duration)
                        ]
                    ).filter(
                        ~ Q(sync_attributes__id__in=lst_attributes) &
                        Q(sync_attributes__id__in=lst_att_delay) &
                        Q(project__id=deploy.project.id)
                    ).exclude(
                        Q(sync_attributes__id__in=deploy.excluded_attributes.all())
                    ).exclude(
                        q_in_domain
                    ).exclude(
                        q_ex_domain
                    ).values('id').distinct().count()
                    duration += 1

                labels.append(loop_date.strftime(date_format))
                provided_data.append({'value': value})
                if loop_date <= now:
                    available_data.append({'value': value})

            lst_attributes += lst_att_delay
            rolling_date = end_horizon.date()

        chart_data[_('Provided')] = provided_data
        chart_data[_('Available')] = available_data

        return Response(
            {
                'data': chart_data,
                'x_labels': list(labels),
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='enabled/project')
    def enabled_by_project(self, request, format=None):
        total = Deployment.objects.scope(request.user.userprofile).filter(
            enabled=True
        ).count()

        values_null = defaultdict(list)
        for item in Deployment.objects.scope(
            request.user.userprofile
        ).filter(
            enabled=True, schedule=None
        ).values(
            'project__id', 'project__name'
        ).annotate(
            count=Count('id')
        ).order_by('project__id', '-count'):
            values_null[item.get('project__id')].append(
                {
                    'name': '{} ({})'.format(_('Without schedule'), item.get('project__name')),
                    'value': item.get('count'),
                    'project_id': item.get('project__id'),
                    'schedule': False
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
            'project__id', 'project__name'
        ).annotate(
            count=Count('id')
        ).order_by('project__id', '-count'):
            values_not_null[item.get('project__id')].append(
                {
                    'name': '{} ({})'.format(_('With schedule'), item.get('project__name')),
                    'value': item.get('count'),
                    'project_id': item.get('project__id'),
                    'schedule': True
                }
            )

        inner = []
        outer = []
        for project in Project.objects.scope(request.user.userprofile).all():
            count = 0
            outer_project = {}
            if project.id in values_null:
                count += values_null[project.id][0]['value']
                outer_project = values_null[project.id][0]
            if project.id in values_not_null:
                count += values_not_null[project.id][0]['value']
                outer_project = values_not_null[project.id][0]
            if count:
                inner.append({
                    'name': project.name,
                    'value': count,
                    'project_id': project.id,
                })
                outer.append(outer_project)

        return Response(
            {
                'title': _('Enabled Deployments'),
                'total': total,
                'inner': inner,
                'outer': outer
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='enabled')
    def by_enabled(self, request, format=None):
        total = Deployment.objects.scope(request.user.userprofile).count()

        values_null = defaultdict(list)
        for item in Deployment.objects.scope(request.user.userprofile).filter(
            enabled=True
        ).values(
            'project__id', 'project__name'
        ).annotate(
            count=Count('id')
        ).order_by('project__id', '-count'):
            values_null[item.get('project__id')].append(
                {
                    'name': '{} ({})'.format(_('Enabled'), item.get('project__name')),
                    'value': item.get('count'),
                    'project_id': item.get('project__id'),
                    'enabled': True,
                }
            )

        values_not_null = defaultdict(list)
        for item in Deployment.objects.scope(request.user.userprofile).filter(
            enabled=False,
        ).values(
            'project__id', 'project__name'
        ).annotate(
            count=Count('id')
        ).order_by('project__id', '-count'):
            values_not_null[item.get('project__id')].append(
                {
                    'name': '{} ({})'.format(_('Disabled'), item.get('project__name')),
                    'value': item.get('count'),
                    'project_id': item.get('project__id'),
                    'enabled': False
                }
            )

        inner = []
        outer = []
        for project in Project.objects.scope(request.user.userprofile).all():
            count = 0
            outer_project = {}
            if project.id in values_null:
                count += values_null[project.id][0]['value']
                outer_project = values_null[project.id][0]
            if project.id in values_not_null:
                count += values_not_null[project.id][0]['value']
                outer_project = values_not_null[project.id][0]
            if count:
                inner.append({
                    'name': project.name,
                    'value': count,
                    'project_id': project.id,
                })
                outer.append(outer_project)

        return Response(
            {
                'title': _('Deployments / Enabled'),
                'total': total,
                'inner': inner,
                'outer': outer
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='schedule')
    def by_schedule(self, request, format=None):
        total = Deployment.objects.scope(request.user.userprofile).count()

        values_null = defaultdict(list)
        for item in Deployment.objects.scope(request.user.userprofile).filter(
            schedule=None
        ).values(
            'project__id', 'project__name'
        ).annotate(
            count=Count('id')
        ).order_by('project__id', '-count'):
            values_null[item.get('project__id')].append(
                {
                    'name': '{} ({})'.format(_('Without schedule'), item.get('project__name')),
                    'value': item.get('count'),
                    'project_id': item.get('project__id'),
                    'schedule': False
                }
            )

        values_not_null = defaultdict(list)
        for item in Deployment.objects.scope(request.user.userprofile).filter(
            ~Q(schedule=None)
        ).values(
            'project__id', 'project__name'
        ).annotate(
            count=Count('id')
        ).order_by('project__id', '-count'):
            values_not_null[item.get('project__id')].append(
                {
                    'name': '{} ({})'.format(_('With schedule'), item.get('project__name')),
                    'value': item.get('count'),
                    'project_id': item.get('project__id'),
                    'schedule': True
                }
            )

        inner = []
        outer = []
        for project in Project.objects.scope(request.user.userprofile).all():
            count = 0
            data_project = []
            outer_project = {}
            if project.id in values_null:
                count += values_null[project.id][0]['value']
                data_project.append(values_null[project.id][0])
                outer_project = values_null[project.id][0]
            if project.id in values_not_null:
                count += values_not_null[project.id][0]['value']
                data_project.append(values_not_null[project.id][0])
                outer_project = values_not_null[project.id][0]
            if count:
                inner.append({
                    'name': project.name,
                    'value': count,
                    'project_id': project.id,
                })
                outer.append(outer_project)

        return Response(
            {
                'title': _('Deployments / Schedule'),
                'total': total,
                'inner': inner,
                'outer': outer
            },
            status=status.HTTP_200_OK
        )
