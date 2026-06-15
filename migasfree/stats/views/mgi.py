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

from collections import defaultdict

from django.db import models
from django.db.models import Count
from django.db.models.functions import ExtractMonth, ExtractYear
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, OpenApiTypes, extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...mgi.models import Build, Config, Flavour
from .events import event_by_month, month_interval


@extend_schema(tags=['stats'])
@permission_classes((permissions.IsAuthenticated,))
class MgiStatsViewSet(viewsets.ViewSet):
    serializer_class = None

    @extend_schema(
        description='Returns statistics for MGI Configurations grouped by build type and project.',
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Configuration count statistics.',
            )
        },
    )
    @action(methods=['get'], detail=False, url_path='build-types')
    def build_types(self, request):
        """Get statistics of configuration build types and project breakdown."""
        user = request.user.userprofile
        total = Config.objects.scope(user).count()

        build_type_choices = dict(Config.BUILD_TYPE_CHOICES)
        type_counts = defaultdict(int)
        outer = []
        for item in (
            Config.objects.scope(user)
            .values('project__id', 'project__name', 'build_type')
            .annotate(count=Count('id'))
            .order_by('build_type', 'project__name')
        ):
            b_type = item.get('build_type')
            type_counts[b_type] += item.get('count')
            outer.append(
                {
                    'name': item.get('project__name'),
                    'value': item.get('count'),
                    'project_id': item.get('project__id'),
                    'build_type': b_type,
                }
            )

        inner = []
        for b_type, count in type_counts.items():
            inner.append(
                {
                    'name': build_type_choices.get(b_type, b_type),
                    'value': count,
                    'build_type': b_type,
                }
            )

        return Response(
            {
                'title': _('MGI Configurations / Build Type'),
                'total': total,
                'inner': inner,
                'outer': outer,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        description='Returns statistics for MGI Builds grouped by success status and specific status codes.',
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Build status count statistics.',
            )
        },
    )
    @action(methods=['get'], detail=False, url_path='build-status')
    def build_status(self, request):
        """Get statistics of build statuses and group breakdown."""
        user = request.user.userprofile
        total = Build.objects.scope(user).count()

        status_counts = defaultdict(int)
        for item in Build.objects.scope(user).values('status').annotate(count=Count('id')):
            status_counts[item.get('status')] = item.get('count')

        success_count = status_counts.get('completed', 0)
        failed_count = status_counts.get('failed', 0)
        active_count = status_counts.get('queued', 0) + status_counts.get('running', 0)

        inner = []
        if success_count:
            inner.append({'name': _('Successful'), 'value': success_count, 'group': 'success'})
        if failed_count:
            inner.append({'name': _('Failed'), 'value': failed_count, 'group': 'failed'})
        if active_count:
            inner.append({'name': _('Active / Pending'), 'value': active_count, 'group': 'active'})

        outer = []
        for s_code, s_label in Build.STATUS_CHOICES:
            count = status_counts.get(s_code, 0)
            if count:
                outer.append(
                    {
                        'name': s_label,
                        'value': count,
                        'status': s_code,
                    }
                )

        return Response(
            {
                'title': _('MGI Builds / Status'),
                'total': total,
                'inner': inner,
                'outer': outer,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        description=(
            'Returns MGI build activity counts grouped by month and project for '
            'the interval defined by the optional begin and end query parameters.'
        ),
        parameters=[
            OpenApiParameter(
                name='begin',
                description='Start month in YYYY-MM format (optional)',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name='end',
                description='End month in YYYY-MM format (optional)',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Monthly build counts grouped by project.',
            )
        },
    )
    @action(methods=['get'], detail=False, url_path='builds/month')
    def builds_by_month(self, request):
        """Get build timeline count statistics grouped by month and project."""
        user = request.user.userprofile
        begin_date, end_date = month_interval(
            begin_month=request.query_params.get('begin', ''), end_month=request.query_params.get('end', '')
        )

        queryset = (
            Build.objects.scope(user)
            .filter(started_at__gte=begin_date, started_at__isnull=False)
            .annotate(
                year=ExtractYear('started_at'),
                month=ExtractMonth('started_at'),
                project_id=models.F('release__config__project_id'),
            )
            .order_by('year', 'month', 'project_id')
            .values('year', 'month', 'project_id')
            .annotate(count=Count('id'))
        )

        data = event_by_month(list(queryset), begin_date, end_date, Build, field='project_id')
        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        description=(
            'Returns build performance metrics including average duration, '
            'average image size, total completed count, and breakdown by build type.'
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Duration and size metrics of completed builds.',
            )
        },
    )
    @action(methods=['get'], detail=False, url_path='build-metrics')
    def build_metrics(self, request):
        """Get performance duration and size metrics of completed builds."""
        user = request.user.userprofile
        builds = Build.objects.scope(user).filter(
            status='completed', started_at__isnull=False, finished_at__isnull=False
        )

        total_completed = builds.count()
        total_duration = 0.0
        total_size = 0
        size_count = 0

        # Loop through pre-fetched records
        build_types_metrics = defaultdict(
            lambda: {'total_duration': 0.0, 'completed_count': 0, 'total_size': 0, 'size_count': 0}
        )

        for build in builds:
            b_type = build.flavour.config.build_type
            duration = (build.finished_at - build.started_at).total_seconds()
            if duration >= 0:
                total_duration += duration
                build_types_metrics[b_type]['total_duration'] += duration
                build_types_metrics[b_type]['completed_count'] += 1
            if build.size is not None:
                total_size += build.size
                size_count += 1
                build_types_metrics[b_type]['total_size'] += build.size
                build_types_metrics[b_type]['size_count'] += 1

        avg_duration = total_duration / total_completed if total_completed > 0 else 0.0
        avg_size = total_size / size_count if size_count > 0 else 0.0

        build_type_choices = dict(Config.BUILD_TYPE_CHOICES)
        type_metrics_list = []
        for b_type, data in build_types_metrics.items():
            completed = data['completed_count']
            s_count = data['size_count']
            type_metrics_list.append(
                {
                    'build_type': b_type,
                    'name': build_type_choices.get(b_type, b_type),
                    'avg_duration': round(data['total_duration'] / completed, 2) if completed > 0 else 0.0,
                    'avg_size': round(data['total_size'] / s_count, 2) if s_count > 0 else 0.0,
                    'total_size': data['total_size'],
                    'completed_count': completed,
                }
            )

        return Response(
            {
                'avg_duration': round(avg_duration, 2),
                'avg_size': round(avg_size, 2),
                'total_size': total_size,
                'total_completed': total_completed,
                'by_build_type': type_metrics_list,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        description='Returns statistics for MGI Flavours grouped by enablement status and project.',
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Flavour enablement statistics.',
            )
        },
    )
    @action(methods=['get'], detail=False, url_path='flavours')
    def flavours(self, request):
        """Get enablement statistics of flavours and project breakdown."""
        user = request.user.userprofile
        total = Flavour.objects.scope(user).count()

        enabled_counts = defaultdict(int)
        outer = []
        for item in (
            Flavour.objects.scope(user)
            .values('config__project__id', 'config__project__name', 'enabled')
            .annotate(count=Count('id'))
            .order_by('config__project__name', '-enabled')
        ):
            proj_id = item.get('config__project__id')
            proj_name = item.get('config__project__name')
            is_enabled = item.get('enabled')
            count = item.get('count')

            enabled_counts[is_enabled] += count
            outer.append(
                {
                    'name': f'{_("Enabled") if is_enabled else _("Disabled")} ({proj_name})',
                    'value': count,
                    'project_id': proj_id,
                    'enabled': is_enabled,
                }
            )

        inner = []
        if True in enabled_counts:
            inner.append({'name': _('Enabled'), 'value': enabled_counts[True], 'enabled': True})
        if False in enabled_counts:
            inner.append({'name': _('Disabled'), 'value': enabled_counts[False], 'enabled': False})

        return Response(
            {
                'title': _('MGI Flavours / Enabled'),
                'total': total,
                'inner': inner,
                'outer': outer,
            },
            status=status.HTTP_200_OK,
        )
