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

from datetime import datetime, timedelta

from django.conf import settings
from django.http import QueryDict
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_redis import get_redis_connection
from rest_framework import viewsets, exceptions, status, mixins, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...core.models import Deployment
from ...device.models import Logical, Driver, Model
from ...hardware.models import Node
from ...app_catalog.models import Policy
from ...core.serializers import PlatformSerializer
from ...core.views import MigasViewSet, ExportViewSet
from ...utils import replace_keys, remove_duplicates_preserving_order

from .. import models, serializers
from ..filters import (
    PackageHistoryFilter, ErrorFilter, NotificationFilter,
    FaultDefinitionFilter, FaultFilter, ComputerFilter,
    MigrationFilter, StatusLogFilter, SynchronizationFilter,
)


@permission_classes((permissions.DjangoModelPermissions,))
class ComputerViewSet(viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = models.Computer.objects.all()
    serializer_class = serializers.ComputerSerializer
    filterset_class = ComputerFilter
    search_fields = settings.MIGASFREE_COMPUTER_SEARCH_FIELDS
    ordering = (settings.MIGASFREE_COMPUTER_SEARCH_FIELDS[0],)

    def get_serializer_class(self):
        if self.action == 'update' or self.action == 'partial_update':
            return serializers.ComputerWriteSerializer

        return serializers.ComputerSerializer

    def get_queryset(self):
        if self.request is None:
            return models.Computer.objects.none()

        user = self.request.user.userprofile
        qs = self.queryset.select_related(
            'project',
            'sync_user',
            'default_logical_device',
            'default_logical_device__feature',
            'default_logical_device__device',
        ).prefetch_related(
            Prefetch('node_set', queryset=Node.objects.filter(parent=None)),
        )
        if not user.is_view_all():
            qs = qs.filter(id__in=user.get_computers())

        return qs

    def partial_update(self, request, *args, **kwargs):
        if isinstance(request.data, QueryDict):
            data = dict(request.data.lists())
        else:
            data = request.data

        devices = data.get(
            'assigned_logical_devices_to_cid[]',
            data.get('assigned_logical_devices_to_cid', None)
        )
        if devices:
            computer = get_object_or_404(models.Computer, pk=kwargs['pk'])

            try:
                assigned_logical_devices_to_cid = list(map(int, devices))
            except ValueError:
                assigned_logical_devices_to_cid = []

            for item in assigned_logical_devices_to_cid:
                logical_device = Logical.objects.get(pk=item)
                model = Model.objects.get(device=logical_device.device)
                if not Driver.objects.filter(
                        feature=logical_device.feature,
                        model=model,
                        project=computer.project
                ):
                    return Response(
                        _('Error in feature %s for assign computer %s.'
                          ' There is no driver defined for project %s in model %s.') % (
                                logical_device.feature,
                                computer,
                                computer.project,
                                "<a href='{}'>{}</a>".format(
                                    reverse(
                                        'admin:server_devicemodel_change',
                                        args=(model.pk,)
                                    ),
                                    model
                                )
                            ),
                        status=status.HTTP_400_BAD_REQUEST,
                        content_type='text/plain'
                    )

            computer.update_logical_devices(assigned_logical_devices_to_cid)

        return super(ComputerViewSet, self).partial_update(
            request,
            *args,
            **kwargs
        )

    @action(methods=['get'], detail=True, url_name='devices')
    def devices(self, request, pk=None):
        computer = get_object_or_404(models.Computer, pk=pk)
        serializer = serializers.ComputerDevicesSerializer(computer, context={'request': request})

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True)
    def label(self, request, pk=None):
        computer = get_object_or_404(models.Computer, pk=pk)

        response = {
            'uuid': computer.uuid,
            'name': computer.name,
            'search': computer.__str__(),
            'helpdesk': settings.MIGASFREE_HELP_DESK,
        }

        return Response(
            response,
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True, url_path='software/inventory', url_name='software_inventory')
    def software_inventory(self, request, pk=None):
        """
        Returns installed packages in a computer
        """
        computer = get_object_or_404(models.Computer, pk=pk)

        data = list(
            computer.packagehistory_set.filter(
                uninstall_date__isnull=True
            ).values(
                'package__id', 'package__fullname',
            ).distinct().order_by('package__fullname')
        )

        return Response(
            replace_keys(
                data,
                {
                    'package__id': 'id',
                    'package__fullname': 'name',
                }
            ),
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True, url_path='software/history', url_name='software_history')
    def software_history(self, request, pk=None):
        """
        Returns software history of a computer
        """
        computer = get_object_or_404(models.Computer, pk=pk)

        return Response(
            computer.get_software_history(),
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=True)
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

    @action(methods=['get'], detail=False, url_path='status')
    def status_choices(self, request, format=None):
        response = {
            'choices': dict(models.Computer.STATUS_CHOICES),
            'productive': models.Computer.PRODUCTIVE_STATUS,
            'unproductive': models.Computer.UNPRODUCTIVE_STATUS,
            'active': models.Computer.ACTIVE_STATUS,
            'subscribed': models.Computer.SUBSCRIBED_STATUS,
            'unsubscribed': models.Computer.UNSUBSCRIBED_STATUS
        }

        return Response(response, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def errors(self, request, pk=None):
        get_object_or_404(models.Computer, pk=pk)

        return Response(
            {
                'unchecked': models.Error.unchecked.filter(computer__pk=pk).count(),
                'total': models.Error.objects.filter(computer__pk=pk).count()
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True)
    def faults(self, request, pk=None):
        get_object_or_404(models.Computer, pk=pk)

        return Response(
            {
                'unchecked': models.Fault.unchecked.filter(computer__pk=pk).count(),
                'total': models.Fault.objects.filter(computer__pk=pk).count()
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=True)
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

    @action(methods=['get'], detail=False)
    def synchronizing(self, request, format=None):
        con = get_redis_connection()

        result = []
        delayed_time = datetime.now() - timedelta(
            seconds=settings.MIGASFREE_SECONDS_MESSAGE_ALERT
        )

        computers = con.smembers('migasfree:watch:msg')
        for computer_id in computers:
            date = con.hget('migasfree:msg:%s' % computer_id, 'date')
            if datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f') > delayed_time:
                result.append(computer_id)

        sync_computers = models.Computer.objects.filter(pk__in=result)

        serializer = serializers.ComputerSerializer(sync_computers, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False)
    def delayed(self, request, format=None):
        con = get_redis_connection()

        result = []
        delayed_time = datetime.now() - timedelta(
            seconds=settings.MIGASFREE_SECONDS_MESSAGE_ALERT
        )

        computers = con.smembers('migasfree:watch:msg')
        for computer_id in computers:
            computer_id = int(computer_id)
            date = con.hget('migasfree:msg:{}'.format(computer_id), 'date')
            if date and datetime.strptime(date.decode(), '%Y-%m-%dT%H:%M:%S.%f') <= delayed_time:
                result.append(computer_id)

        delayed_computers = models.Computer.objects.filter(pk__in=result)

        serializer = serializers.ComputerSerializer(
            delayed_computers, many=True,
            context={'request': request}
        )
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True)
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
        serializer = serializers.ComputerSyncSerializer(computer, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def situation(self, request, pk=None):
        """
        :param request
            date
        :param pk: computer id
        :return:
            {
                "platform": {
                    "id": x,
                    "name": "xxx"
                },
                "project": {
                    "id": x,
                    "name": "xxx"
                },
                "status": "xxx"
            }
        """
        user = request.user.userprofile
        computer = get_object_or_404(models.Computer, pk=pk)
        date = request.GET.get('date', datetime.now())

        migration = models.Migration.situation(computer.id, date, user)
        status_log = models.StatusLog.situation(computer.id, date, user)

        response = {}
        if migration:
            serializer = PlatformSerializer(migration.project.platform, context={'request': request})
            response['platform'] = serializer.data

            serializer = serializers.ProjectInfoSerializer(migration.project, context={'request': request})
            response['project'] = serializer.data

        if status_log:
            response['status'] = status_log.status
        else:
            if isinstance(date, str):
                date = datetime.strptime(date, '%Y-%m-%d')
                if date >= computer.created_at:
                    response['status'] = settings.MIGASFREE_DEFAULT_COMPUTER_STATUS

        return Response(response, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True, url_path='sync/simulation')
    def simulate_sync(self, request, pk=None):
        computer = get_object_or_404(models.Computer, pk=pk)
        user = request.user
        user.userprofile.check_scope(pk)

        repos = Deployment.available_deployments(
            computer, computer.get_all_attributes()
        ).values('id', 'name')
        definitions = models.FaultDefinition.enabled_for_attributes(
            computer.get_all_attributes()
        ).values('id', 'name')

        pkgs = Deployment.available_deployments(
            computer, computer.get_all_attributes()
        ).values_list('packages_to_install', 'packages_to_remove')

        install = []
        remove = []
        for install_item, remove_item in pkgs:
            if install_item:
                install = [x for x in install_item.split('\n') if x]

            if remove_item:
                remove = [x for x in remove_item.split('\n') if x]

        packages = {
            'install': remove_duplicates_preserving_order(install),
            'remove': remove_duplicates_preserving_order(remove)
        }

        policy_pkg_to_install, policy_pkg_to_remove = Policy.get_packages(computer)
        policies = {
            'install': policy_pkg_to_install,
            'remove': policy_pkg_to_remove
        }

        capture = computer.hardware_capture_is_required()

        logical_devices = []
        for device in computer.logical_devices():
            logical_devices.append(device.as_dict(computer.project))

        if computer.default_logical_device:
            default_logical_device = computer.default_logical_device.id
        else:
            default_logical_device = 0

        response = {
            'deployments': repos,
            'fault_definitions': definitions,
            'packages': packages,
            'policies': policies,
            'capture_hardware': capture,
            'logical_devices': logical_devices,
            'default_logical_device': default_logical_device
        }

        return Response(response, status=status.HTTP_200_OK)


@permission_classes((permissions.DjangoModelPermissions,))
class ErrorViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin, mixins.DestroyModelMixin,
    viewsets.GenericViewSet, MigasViewSet
):
    queryset = models.Error.objects.all()
    serializer_class = serializers.ErrorSerializer
    filterset_class = ErrorFilter
    search_fields = ['created_at', 'description']
    ordering_fields = '__all__'
    ordering = ('-created_at',)

    def get_serializer_class(self):
        if self.action == 'update' or self.action == 'partial_update':
            return serializers.ErrorWriteSerializer

        return serializers.ErrorSerializer

    def get_queryset(self):
        if self.request is None:
            return models.Error.objects.none()

        user = self.request.user.userprofile
        qs = self.queryset.select_related(
            'project',
            'computer',
        )
        if not user.is_view_all():
            qs = qs.filter(
                project_id__in=user.get_projects(),
                computer_id__in=user.get_computers()
            )

        return qs


@permission_classes((permissions.DjangoModelPermissions,))
class FaultDefinitionViewSet(viewsets.ModelViewSet, MigasViewSet):
    queryset = models.FaultDefinition.objects.all()
    serializer_class = serializers.FaultDefinitionSerializer
    filterset_class = FaultDefinitionFilter
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return serializers.FaultDefinitionWriteSerializer

        return serializers.FaultDefinitionSerializer


@permission_classes((permissions.DjangoModelPermissions,))
class FaultViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin, mixins.DestroyModelMixin,
    viewsets.GenericViewSet, MigasViewSet
):
    queryset = models.Fault.objects.all()
    serializer_class = serializers.FaultSerializer
    filterset_class = FaultFilter
    search_fields = ['created_at', 'result']
    ordering_fields = '__all__'
    ordering = ('-created_at',)

    def get_serializer_class(self):
        if self.action == 'update' or self.action == 'partial_update':
            return serializers.FaultWriteSerializer

        return serializers.FaultSerializer

    def get_queryset(self):
        if self.request is None:
            return models.Fault.objects.none()

        user = self.request.user.userprofile
        qs = self.queryset.select_related(
            'project',
            'fault_definition',
            'computer',
        )
        if not user.is_view_all():
            qs = qs.filter(
                project_id__in=user.get_projects(),
                computer_id__in=user.get_computers()
            )

        return qs

    @action(methods=['get'], detail=False, url_path='user')
    def user_choices(self, request, format=None):
        response = {
            'choices': dict(models.Fault.USER_FILTER_CHOICES),
        }

        return Response(response, status=status.HTTP_200_OK)


@permission_classes((permissions.DjangoModelPermissions,))
class MigrationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin, viewsets.GenericViewSet,
    MigasViewSet
):
    queryset = models.Migration.objects.all()
    serializer_class = serializers.MigrationSerializer
    filterset_class = MigrationFilter
    ordering_fields = '__all__'
    ordering = ('-created_at',)

    def get_queryset(self):
        if self.request is None:
            return models.Migration.objects.none()

        user = self.request.user.userprofile
        qs = self.queryset.select_related(
            'project',
            'computer',
        )
        if not user.is_view_all():
            qs = qs.filter(
                project_id__in=user.get_projects(),
                computer_id__in=user.get_computers()
            )

        return qs


@permission_classes((permissions.DjangoModelPermissions,))
class NotificationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin, mixins.DestroyModelMixin,
    viewsets.GenericViewSet, MigasViewSet
):
    queryset = models.Notification.objects.all()
    serializer_class = serializers.NotificationSerializer
    filterset_class = NotificationFilter
    search_fields = ['message']
    ordering_fields = '__all__'
    ordering = ('-created_at',)

    def get_serializer_class(self):
        if self.action == 'update' or self.action == 'partial_update':
            return serializers.NotificationWriteSerializer

        return serializers.NotificationSerializer


@permission_classes((permissions.DjangoModelPermissions,))
class PackageHistoryViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    viewsets.GenericViewSet, MigasViewSet
):
    queryset = models.PackageHistory.objects.all()
    serializer_class = serializers.PackageHistorySerializer
    filterset_class = PackageHistoryFilter
    ordering_fields = '__all__'
    ordering = ('computer', 'package__fullname',)


@permission_classes((permissions.DjangoModelPermissions,))
class StatusLogViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin, viewsets.GenericViewSet,
    MigasViewSet
):
    queryset = models.StatusLog.objects.all()
    serializer_class = serializers.StatusLogSerializer
    filterset_class = StatusLogFilter
    search_fields = ['status']
    ordering_fields = '__all__'
    ordering = ('-created_at',)

    def get_queryset(self):
        if self.request is None:
            return models.StatusLog.objects.none()

        user = self.request.user.userprofile
        qs = self.queryset.select_related(
            'computer',
        )
        if not user.is_view_all():
            qs = qs.filter(computer_id__in=user.get_computers())

        return qs


@permission_classes((permissions.DjangoModelPermissions,))
class SynchronizationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin, viewsets.GenericViewSet,
    MigasViewSet
):
    queryset = models.Synchronization.objects.all()
    serializer_class = serializers.SynchronizationSerializer
    filterset_class = SynchronizationFilter
    search_fields = ['user__name', 'user__fullname']
    ordering_fields = '__all__'
    ordering = ('-created_at',)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' \
                or self.action == 'partial_update':
            return serializers.SynchronizationWriteSerializer

        return serializers.SynchronizationSerializer

    def get_queryset(self):
        if self.request is None:
            return models.Synchronization.objects.none()

        user = self.request.user.userprofile
        qs = self.queryset.select_related(
            'computer',
            'project',
            'user',
        )
        if not user.is_view_all():
            qs = qs.filter(
                project_id__in=user.get_projects(),
                computer_id__in=user.get_computers()
            )

        return qs


@permission_classes((permissions.DjangoModelPermissions,))
class UserViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin, viewsets.GenericViewSet,
    MigasViewSet
):
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_queryset(self):
        if self.request is None:
            return models.User.objects.none()

        user = self.request.user.userprofile
        qs = self.queryset
        if not user.is_view_all():
            qs = qs.filter(computer__in=user.get_computers())

        return qs
