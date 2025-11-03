# -*- coding: UTF-8 -*-

# Copyright (c) 2015-2025 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2025 Alberto Gacías <alberto@migasfree.org>
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

import csv
import json

from datetime import datetime
from operator import gt, le

from django.core.paginator import Paginator
from django.conf import settings
from django.http import QueryDict, HttpResponse
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_redis import get_redis_connection
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, exceptions, status, mixins, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.utils.urls import remove_query_param, replace_query_param

from ...core.models import Deployment, Attribute
from ...device.models import Logical, Driver, Model
from ...device.serializers import LogicalInfoSerializer
from ...hardware.models import Node
from ...hardware.serializers import NodeOnlySerializer
from ...app_catalog.models import Policy
from ...core.serializers import PlatformSerializer
from ...core.views import MigasViewSet, ExportViewSet
from ...stats.utils import filter_computers_by_date
from ...mixins import DatabaseCheckMixin
from ...paginations import DefaultPagination
from ...utils import replace_keys, decode_dict

from .. import models, serializers
from ..filters import (
    PackageHistoryFilter, ErrorFilter, NotificationFilter,
    FaultDefinitionFilter, FaultFilter, ComputerFilter,
    MigrationFilter, StatusLogFilter, SynchronizationFilter,
    UserFilter,
)
from .safe import remove_computer_messages


@extend_schema(tags=['computers'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: settings.MIGASFREE_COMPUTER_SEARCH_FIELDS, sync_user__name, sync_user__fullname',
            type=str
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class ComputerViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = models.Computer.objects.all()
    serializer_class = serializers.ComputerSerializer
    filterset_class = ComputerFilter
    search_fields = settings.MIGASFREE_COMPUTER_SEARCH_FIELDS + (
        'sync_user__name', 'sync_user__fullname',
    )
    ordering = (settings.MIGASFREE_COMPUTER_SEARCH_FIELDS[0],)

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return serializers.ComputerWriteSerializer

        if self.action == 'list':
            return serializers.ComputerListSerializer

        return serializers.ComputerSerializer

    def get_queryset(self):
        if self.request is None:
            return models.Computer.objects.none()

        return models.Computer.objects.scope(
            self.request.user.userprofile
        ).prefetch_related(
            'tags',
            Prefetch('node_set', queryset=Node.objects.filter(parent=None)),
        )

    def partial_update(self, request, *args, **kwargs):
        if isinstance(request.data, QueryDict):
            data = dict(request.data.lists())
        else:
            data = request.data

        devices = data.get(
            'assigned_logical_devices_to_cid[]',
            data.get('assigned_logical_devices_to_cid', None)
        )
        if devices or isinstance(devices, list):
            computer = get_object_or_404(models.Computer, pk=kwargs['pk'])

            try:
                assigned_logical_devices_to_cid = list(map(int, devices))
            except ValueError:
                assigned_logical_devices_to_cid = []

            for item in assigned_logical_devices_to_cid:
                logical_device = Logical.objects.get(pk=item)
                model = Model.objects.get(device=logical_device.device)
                if not Driver.objects.filter(
                    capability=logical_device.capability,
                    model=model,
                    project=computer.project
                ).exists():
                    return Response(
                        {
                            'error': _(
                                'Error in capability %s for assign computer %s.'
                                ' There is no driver defined for project %s in model %s.'
                            ) % (
                                logical_device.capability,
                                computer,
                                computer.project,
                                model
                            ),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            computer.update_logical_devices(assigned_logical_devices_to_cid)

        return super().partial_update(request, *args, **kwargs)

    @action(methods=['get'], detail=True, url_name='devices')
    def devices(self, request, pk=None):
        computer = self.get_object()
        serializer = serializers.ComputerDevicesSerializer(
            computer, context={'request': request}
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True)
    def label(self, request, pk=None):
        computer = self.get_object()

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

    @action(methods=['get', 'delete'], detail=True, url_path='software/inventory', url_name='software_inventory')
    def software_inventory(self, request, pk=None):
        """
        Returns installed packages in a computer
        """
        computer = self.get_object()

        if request.method == 'DELETE' and request.user.is_superuser:
            computer.packagehistory_set.filter(
                uninstall_date__isnull=True,
                package__project=computer.project
            ).delete()

        data = list(
            computer.packagehistory_set.filter(
                uninstall_date__isnull=True,
                package__project=computer.project
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

    @action(methods=['get', 'delete'], detail=True, url_path='software/history', url_name='software_history')
    def software_history(self, request, pk=None):
        """
        Returns software history of a computer
        """
        computer = self.get_object()

        if request.method == 'DELETE' and request.user.is_superuser:
            computer.delete_software_history(request.GET.get('key', None))

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
        computer = self.get_object()

        ret = computer.change_status(request.data.get('status'))
        if not ret:
            raise exceptions.ParseError(
                _('Status must have one of the values: %s') % (
                    dict(models.Computer.STATUS_CHOICES).keys()
                )
            )

        serializer = serializers.ComputerSerializer(computer, context={'request': request})
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='status')
    def status_choices(self, request):
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
        self.get_object()

        return Response(
            {
                'unchecked': models.Error.unchecked.filter(computer__pk=pk).count(),
                'total': models.Error.objects.filter(computer__pk=pk).count()
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True)
    def faults(self, request, pk=None):
        self.get_object()

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
        Exchanges tags, status and devices
        """
        source = self.get_object()
        target = get_object_or_404(
            models.Computer, id=request.data.get('target')
        )

        models.Computer.replacement(source, target)

        return Response(status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def synchronizing(self, request):
        result, _ = filter_computers_by_date(gt)
        sync_computers = models.Computer.objects.filter(pk__in=result)

        serializer = serializers.ComputerSerializer(sync_computers, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False)
    def delayed(self, request):
        result, _ = filter_computers_by_date(le)
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
        computer = self.get_object()
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
        computer = self.get_object()
        date = request.GET.get('date', timezone.localtime(timezone.now()))

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
        computer = self.get_object()
        user = request.user
        user.userprofile.check_scope(pk)

        repos = Deployment.available_deployments(
            computer, computer.get_all_attributes()
        ).values('id', 'name', 'source')
        definitions = models.FaultDefinition.enabled_for_attributes(
            computer.get_all_attributes()
        ).values('id', 'name')

        pkgs = Deployment.available_deployments(
            computer, computer.get_all_attributes()
        ).values_list('packages_to_install', 'packages_to_remove', 'name', 'id')

        install = set()
        remove = set()
        for install_item, remove_item, deploy_name, deploy_id in pkgs:
            if install_item:
                for pkg in install_item.split('\n'):
                    if pkg:
                        install.add(json.dumps({
                            'package': pkg,
                            'name': deploy_name,
                            'id': deploy_id
                        }, sort_keys=True))

            if remove_item:
                for pkg in remove_item.split('\n'):
                    if pkg:
                        remove.add(json.dumps({
                            'package': pkg,
                            'name': deploy_name,
                            'id': deploy_id
                        }, sort_keys=True))

        packages = {
            'install': [json.loads(x) for x in install],
            'remove': [json.loads(x) for x in remove]
        }

        policy_pkg_to_install, policy_pkg_to_remove = Policy.get_packages(computer)
        policies = {
            'install': policy_pkg_to_install,
            'remove': policy_pkg_to_remove
        }

        capture = computer.hardware_capture_is_required()

        logical_devices = []
        for device in computer.logical_devices():
            logical_devices.append(LogicalInfoSerializer(device).data)

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

    @action(methods=['get'], detail=True)
    def hardware(self, request, pk=None):
        computer = self.get_object()
        request.user.userprofile.check_scope(pk)

        results = Node.objects.filter(computer=computer).order_by(
            'id', 'parent_id', 'level'
        )

        return Response(
            NodeOnlySerializer(results, many=True).data,
            status=status.HTTP_200_OK
        )


@extend_schema(tags=['errors'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: created_at, description',
            type=str
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class ErrorViewSet(
    DatabaseCheckMixin,
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin, mixins.DestroyModelMixin,
    viewsets.GenericViewSet, MigasViewSet, ExportViewSet
):
    queryset = models.Error.objects.all()
    serializer_class = serializers.ErrorSerializer
    filterset_class = ErrorFilter
    search_fields = ['created_at', 'description']
    ordering_fields = '__all__'
    ordering = ('-created_at',)

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return serializers.ErrorWriteSerializer

        return serializers.ErrorSerializer

    def get_queryset(self):
        if self.request is None:
            return models.Error.objects.none()

        return models.Error.objects.scope(self.request.user.userprofile)


@extend_schema(tags=['fault-definitions'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: name',
            type=str
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class FaultDefinitionViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = models.FaultDefinition.objects.all()
    serializer_class = serializers.FaultDefinitionSerializer
    filterset_class = FaultDefinitionFilter
    search_fields = ['name']
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return serializers.FaultDefinitionWriteSerializer

        return serializers.FaultDefinitionSerializer

    def get_queryset(self):
        if self.request is None:
            return models.FaultDefinition.objects.none()

        qs = Attribute.objects.scope(self.request.user.userprofile)

        return models.FaultDefinition.objects.scope(
            self.request.user.userprofile
        ).prefetch_related(
            Prefetch('included_attributes', queryset=qs),
            Prefetch('excluded_attributes', queryset=qs),
            'included_attributes__property_att',
            'excluded_attributes__property_att',
            'users',
        )


@extend_schema(tags=['faults'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: created_at, result',
            type=str
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class FaultViewSet(
    DatabaseCheckMixin,
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin, mixins.DestroyModelMixin,
    viewsets.GenericViewSet, MigasViewSet, ExportViewSet
):
    queryset = models.Fault.objects.all()
    serializer_class = serializers.FaultSerializer
    filterset_class = FaultFilter
    search_fields = ['created_at', 'result']
    ordering_fields = '__all__'
    ordering = ('-created_at',)

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return serializers.FaultWriteSerializer

        return serializers.FaultSerializer

    def get_queryset(self):
        if self.request is None:
            return models.Fault.objects.none()

        return models.Fault.objects.scope(self.request.user.userprofile)

    @action(methods=['get'], detail=False, url_path='user')
    def user_choices(self, request):
        response = {
            'choices': dict(models.Fault.USER_FILTER_CHOICES),
        }

        return Response(response, status=status.HTTP_200_OK)


@extend_schema(tags=['migrations'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: computer__name, computer__id',
            type=str
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class MigrationViewSet(
    DatabaseCheckMixin,
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin, viewsets.GenericViewSet,
    MigasViewSet, ExportViewSet
):
    queryset = models.Migration.objects.all()
    serializer_class = serializers.MigrationSerializer
    filterset_class = MigrationFilter
    search_fields = ['computer__name', 'computer__id']
    ordering_fields = '__all__'
    ordering = ('-created_at',)

    def get_queryset(self):
        if self.request is None:
            return models.Migration.objects.none()

        return models.Migration.objects.scope(self.request.user.userprofile)


@extend_schema(tags=['notifications'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: message',
            type=str
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class NotificationViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = models.Notification.objects.all()
    serializer_class = serializers.NotificationSerializer
    filterset_class = NotificationFilter
    search_fields = ['message']
    ordering_fields = '__all__'
    ordering = ('-created_at',)

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return serializers.NotificationWriteSerializer

        if self.action == 'create':
            return serializers.NotificationCreateSerializer

        return serializers.NotificationSerializer


@extend_schema(tags=['packages-history'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: computer__name, package__fullname',
            type=str
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class PackageHistoryViewSet(
    DatabaseCheckMixin,
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    viewsets.GenericViewSet, MigasViewSet, ExportViewSet
):
    queryset = models.PackageHistory.objects.all()
    serializer_class = serializers.PackageHistorySerializer
    filterset_class = PackageHistoryFilter
    search_fields = ['computer__name', 'package__fullname']
    ordering_fields = '__all__'
    ordering = ('computer__name', 'package__fullname',)

    def get_queryset(self):
        if self.request is None:
            return models.PackageHistory.objects.none()

        return models.PackageHistory.objects.scope(self.request.user.userprofile)


@extend_schema(tags=['status-logs'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: status, computer__name',
            type=str
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class StatusLogViewSet(
    DatabaseCheckMixin,
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin, viewsets.GenericViewSet,
    MigasViewSet, ExportViewSet
):
    queryset = models.StatusLog.objects.all()
    serializer_class = serializers.StatusLogSerializer
    filterset_class = StatusLogFilter
    search_fields = ['status', 'computer__name']
    ordering_fields = '__all__'
    ordering = ('-created_at',)

    def get_queryset(self):
        if self.request is None:
            return models.StatusLog.objects.none()

        return models.StatusLog.objects.scope(self.request.user.userprofile)


@extend_schema(tags=['syncs'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: user__name, user__fullname',
            type=str
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class SynchronizationViewSet(
    DatabaseCheckMixin,
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin, viewsets.GenericViewSet,
    MigasViewSet, ExportViewSet
):
    queryset = models.Synchronization.objects.all()
    serializer_class = serializers.SynchronizationSerializer
    filterset_class = SynchronizationFilter
    search_fields = ['user__name', 'user__fullname', 'computer__name', 'consumer']
    ordering_fields = '__all__'
    ordering = ('-created_at',)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return serializers.SynchronizationWriteSerializer

        return serializers.SynchronizationSerializer

    def get_queryset(self):
        if self.request is None:
            return models.Synchronization.objects.none()

        return models.Synchronization.objects.scope(self.request.user.userprofile)


@extend_schema(tags=['users'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: name, fullname',
            type=str
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class UserViewSet(
    DatabaseCheckMixin,
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin, viewsets.GenericViewSet,
    MigasViewSet, ExportViewSet
):
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer
    filterset_class = UserFilter
    search_fields = ['name', 'fullname']
    ordering_fields = '__all__'
    ordering = ('name',)

    def get_queryset(self):
        if self.request is None:
            return models.User.objects.none()

        return models.User.objects.scope(self.request.user.userprofile)


@extend_schema(tags=['messages'])
@permission_classes((permissions.IsAuthenticated,))
class MessageViewSet(viewsets.ViewSet):
    serializer_class = None

    def get_queryset(self):
        id_filter = self.request.query_params.get('id__in', None)
        if id_filter:
            id_filter = list(map(int, id_filter.split(',')))
        project_filter = self.request.query_params.get('project__id', None)
        created_at_lt_filter = self.request.query_params.get('created_at__lt', None)
        created_at_gte_filter = self.request.query_params.get('created_at__gte', None)
        status_filter = self.request.query_params.get('computer__status__in', None)
        search_filter = self.request.query_params.get('search', None)

        con = get_redis_connection()
        items = list(con.smembers('migasfree:watch:msg'))

        projects = []
        computers = []
        user = self.request.user.userprofile
        if user and not user.is_view_all():
            projects = user.get_projects()
            computers = user.get_computers()

        results = []
        for key in items:
            item = decode_dict(con.hgetall(f'migasfree:msg:{int(key)}'))

            if projects and int(item['project_id']) not in projects:
                continue

            if computers and int(item['computer_id']) not in computers:
                continue

            if id_filter and int(key) not in id_filter:
                continue

            if project_filter and int(item['project_id']) != project_filter:
                continue

            if created_at_lt_filter and item['date'] >= created_at_lt_filter:
                continue

            if created_at_gte_filter and item['date'] < created_at_gte_filter:
                continue

            if status_filter and item['computer_status'] not in status_filter:
                continue

            if search_filter and search_filter.lower() not in item['msg'].lower():
                continue

            results.append({
                'id': int(key),
                'created_at': item['date'],
                'computer': {
                    'id': int(item['computer_id']),
                    '__str__': item['computer_name'],
                    'status': item['computer_status'],
                    'summary': item['computer_summary']
                },
                'project': {
                    'id': int(item['project_id']),
                    'name': item['project_name']
                },
                'user': {
                    'id': int(item['user_id']),
                    'name': item['user_name']
                },
                'message': item['msg']
            })

        return sorted(results, key=lambda d: d['created_at'], reverse=True)

    def _get_next_link(self, request, page):
        if not page.has_next():
            return None

        url = request.build_absolute_uri()
        page_number = page.next_page_number()

        return replace_query_param(url, 'page', page_number)

    def _get_previous_link(self, request, page):
        if not page.has_previous():
            return None

        url = self.request.build_absolute_uri()
        page_number = page.previous_page_number()
        if page_number == 1:
            return remove_query_param(url, 'page')

        return replace_query_param(url, 'page', page_number)

    def list(self, request):
        results = self.get_queryset()

        paginator = Paginator(
            results,
            request.GET.get('page_size', DefaultPagination.page_size)
        )
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        return Response(
            {
                'results': page_obj.object_list,
                'count': len(results),
                'next': self._get_next_link(request, page_obj),
                'previous': self._get_previous_link(request, page_obj)
            }
        )

    def destroy(self, request, pk=None):
        remove_computer_messages(int(pk))

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=False)
    def export(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="messages.csv"'

        writer = csv.DictWriter(
            response,
            fieldnames=[
                'created_at',
                'computer__id', 'computer____str__', 'computer__status', 'computer__summary',
                'project__id', 'project__name', 'user__id', 'user__name', 'message',
            ]
        )
        writer.writeheader()

        for item in self.get_queryset():
            writer.writerow({
                'created_at': item['created_at'],
                'computer__id': item['computer']['id'],
                'computer____str__': item['computer']['__str__'],
                'computer__status': item['computer']['status'],
                'computer__summary': item['computer']['summary'],
                'project__id': item['project']['id'],
                'project__name': item['project']['name'],
                'user__id': item['user']['id'],
                'user__name': item['user']['name'],
                'message': item['message'],
            })

        return response
