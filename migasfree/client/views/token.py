# -*- coding: UTF-8 -*-

# Copyright (c) 2015 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015 Alberto Gacías <alberto@migasfree.org>
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
from django.utils.translation import ugettext_lazy as _
from rest_framework import viewsets, exceptions, status, mixins, filters
from rest_framework.decorators import detail_route
from rest_framework.response import Response
# from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_filters import backends

from .. import models, serializers
from ..filters import PackageFilter, ErrorFilter, NotificationFilter


class ComputerViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = models.Computer.objects.all()
    serializer_class = serializers.ComputerSerializer

    """
    def update(request, *args, **kwargs):
        # TODO is_computer_changed(computer, name, project, ip_address, uuid)
        pass

    def partial_update(request, *args, **kwargs):
        pass
    """

    @detail_route(methods=['get'])
    def packages(self, request, pk=None):
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

    @detail_route(methods=['post'])
    def status(self, request, pk=None):
        """
        Input: {
            'status': 'available' | 'reserved' | 'unsubscribed' | 'unkown' | 'intended'
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


class ErrorViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = models.Error.objects.all()
    serializer_class = serializers.ErrorSerializer
    filter_backends = (
        filters.OrderingFilter, backends.DjangoFilterBackend, ErrorFilter
    )
    ordering_fields = '__all__'
    ordering = ('-created_at',)


class FaultViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = models.Fault.objects.all()
    serializer_class = serializers.FaultSerializer


class PackageViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = models.Package.objects.all()
    serializer_class = serializers.PackageSerializer
    filter_backends = (
        filters.OrderingFilter, backends.DjangoFilterBackend, PackageFilter
    )
    ordering_fields = '__all__'
    ordering = ('fullname',)


class NotificationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = models.Notification.objects.all()
    serializer_class = serializers.NotificationSerializer
    filter_backends = (
        filters.OrderingFilter, backends.DjangoFilterBackend, NotificationFilter
    )
    ordering_fields = '__all__'
    ordering = ('-created_at',)
