# -*- coding: UTF-8 -*-

# Copyright (c) 2015-2017 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2017 Alberto Gacías <alberto@migasfree.org>
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

from datetime import datetime, timedelta

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django_redis import get_redis_connection
from rest_framework import viewsets, exceptions, status, mixins, filters
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
# from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_filters import backends

from .. import models, serializers
from ..filters import (
    PackageFilter, ErrorFilter, NotificationFilter,
    FaultDefinitionFilter, FaultFilter, ComputerFilter,
    MigrationFilter, StatusLogFilter, SynchronizationFilter,
)


class ComputerViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = models.Computer.objects.all()
    serializer_class = serializers.ComputerSerializer
    filter_class = ComputerFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)

    """
    def update(request, *args, **kwargs):
        # TODO is_computer_changed(computer, name, project, ip_address, uuid)
        pass

    def partial_update(request, *args, **kwargs):
        pass
    """

    @detail_route(methods=['get'], url_path='software/inventory')
    def software_inventory(self, request, pk=None):
        """
        Returns installed packages in a computer
        """
        computer = get_object_or_404(models.Computer, pk=pk)

        serializer = serializers.PackageSerializer(
            computer.software_inventory.all(), many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @detail_route(methods=['get'], url_path='software/history')
    def software_history(self, request, pk=None):
        """
        Returns software history of a computer
        """
        computer = get_object_or_404(models.Computer, pk=pk)

        return Response(
            computer.software_history,
            status=status.HTTP_200_OK
        )

    @detail_route(methods=['post'])
    def status(self, request, pk=None):
        """
        Input: {
            'status': 'available' | 'reserved' | 'unsubscribed'
                | 'unknown' | 'intended'
        }
        Changes computer status
        """
        computer = get_object_or_404(models.Computer, pk=pk)

        ret = computer.change_status(request.data.get('status'))
        if not ret:
            raise exceptions.ParseError(
                _('Status must have one of the values: %s') % (
                    dict(models.Computer.STATUS_CHOICES).keys()
                )
            )

        serializer = serializers.ComputerSerializer(computer)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @detail_route(methods=['post'])
    def replacement(self, request, pk=None):
        """
        Input: {
            'target': id
        }
        Exchanges tags and status
        """
        source = get_object_or_404(models.Computer, pk=pk)
        target = get_object_or_404(
            models.Computer, id=request.data.get('target')
        )

        models.Computer.replacement(source, target)

        return Response(status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def synchronizing(self, request, format=None):
        con = get_redis_connection('default')

        result = []
        delayed_time = datetime.now() - timedelta(
            seconds=settings.MIGASFREE_SECONDS_MESSAGE_ALERT
        )

        computers = con.smembers('migasfree:watch:msg')
        for computer_id in computers:
            date = con.hget('migasfree:msg:%s' % computer_id, 'date')
            if datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f') > delayed_time:
                result.append(computer_id)

        sync_computers = models.Computer.objects.filter(pk__in=result)

        serializer = serializers.ComputerSerializer(sync_computers, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @list_route(methods=['get'])
    def delayed(self, request, format=None):
        con = get_redis_connection('default')

        result = []
        delayed_time = datetime.now() - timedelta(
            seconds=settings.MIGASFREE_SECONDS_MESSAGE_ALERT
        )

        computers = con.smembers('migasfree:watch:msg')
        for computer_id in computers:
            date = con.hget('migasfree:msg:%s' % computer_id, 'date')
            if datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f') <= delayed_time:
                result.append(computer_id)

        delayed_computers = models.Computer.objects.filter(pk__in=result)

        serializer = serializers.ComputerSerializer(delayed_computers, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @detail_route(methods=['get'])
    def sync(self, request, pk=None):
        """
        :returns
            {
                "date": "Y-m-d H:M:s",
                "user": {
                    "id": x,
                    "name": "xxx",
                    "fullname": "xxxxx"
                },
                "attributes": [
                    {
                        "id": x,
                        "value": "xxx",
                        "description": "xxxxx",
                        "total_computers"; xx,
                        "property_att": {
                            "id": x,
                            "prefix": "xxx"
                        }
                    },
                    ...
                ]
            }
        """
        computer = get_object_or_404(models.Computer, pk=pk)
        serializer = serializers.ComputerSyncSerializer(computer)

        return Response(serializer.data, status=status.HTTP_200_OK)


class ErrorViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = models.Error.objects.all()
    serializer_class = serializers.ErrorSerializer
    filter_class = ErrorFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)
    ordering_fields = '__all__'
    ordering = ('-created_at',)


class FaultDefinitionViewSet(viewsets.ModelViewSet):
    queryset = models.FaultDefinition.objects.all()
    serializer_class = serializers.FaultDefinitionSerializer
    filter_class = FaultDefinitionFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)


class FaultViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = models.Fault.objects.all()
    serializer_class = serializers.FaultSerializer
    filter_class = FaultFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)
    ordering_fields = '__all__'
    ordering = ('-created_at',)


class MigrationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = models.Migration.objects.all()
    serializer_class = serializers.MigrationSerializer
    filter_class = MigrationFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)
    ordering_fields = '__all__'
    ordering = ('-created_at',)


class NotificationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = models.Notification.objects.all()
    serializer_class = serializers.NotificationSerializer
    filter_class = NotificationFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)
    ordering_fields = '__all__'
    ordering = ('-created_at',)


class PackageViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = models.Package.objects.all()
    serializer_class = serializers.PackageSerializer
    filter_class = PackageFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)
    ordering_fields = '__all__'
    ordering = ('fullname',)


class StatusLogViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = models.StatusLog.objects.all()
    serializer_class = serializers.StatusLogSerializer
    filter_class = StatusLogFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)
    ordering_fields = '__all__'
    ordering = ('-created_at',)


class SynchronizationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = models.Synchronization.objects.all()
    serializer_class = serializers.SynchronizationSerializer
    filter_class = SynchronizationFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)
    ordering_fields = '__all__'
    ordering = ('-created_at',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return serializers.SynchronizationWriteSerializer

        return serializers.SynchronizationSerializer
