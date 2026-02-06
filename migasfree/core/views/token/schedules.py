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

from django.db.models import Prefetch
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, viewsets
from rest_framework.decorators import permission_classes

from ....mixins import DatabaseCheckMixin
from ...filters import ScheduleDelayFilter, ScheduleFilter
from ...models import Attribute, Schedule, ScheduleDelay
from ...serializers import (
    ScheduleDelaySerializer,
    ScheduleDelayWriteSerializer,
    ScheduleSerializer,
    ScheduleWriteSerializer,
)
from .base import ExportViewSet, MigasViewSet


@extend_schema(tags=['schedule-delays'])
@permission_classes((permissions.DjangoModelPermissions,))
class ScheduleDelayViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet):
    queryset = ScheduleDelay.objects.all()
    serializer_class = ScheduleDelaySerializer
    filterset_class = ScheduleDelayFilter
    ordering_fields = '__all__'
    ordering = ('delay',)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return ScheduleDelayWriteSerializer

        return ScheduleDelaySerializer

    def get_queryset(self):
        if self.request is None:
            return ScheduleDelay.objects.none()

        qs = Attribute.objects.scope(self.request.user.userprofile)

        return ScheduleDelay.objects.scope(self.request.user.userprofile).prefetch_related(
            Prefetch('attributes', queryset=qs), 'attributes__property_att', 'schedule'
        )


@extend_schema(tags=['schedules'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: name',
            type=str,
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class ScheduleViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = Schedule.objects.prefetch_related(
        'delays',
        'delays__attributes',
        'deployment_set',
    )
    serializer_class = ScheduleSerializer
    filterset_class = ScheduleFilter
    search_fields = ('name',)
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return ScheduleWriteSerializer

        return ScheduleSerializer

    def get_queryset(self):
        if self.request is None:
            return Schedule.objects.none()

        return self.queryset.prefetch_related('delays')
