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

import json
from datetime import datetime
from operator import gt, le

from django.conf import settings
from django.db.models import Prefetch
from django.http import QueryDict
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import exceptions, permissions, status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ....app_catalog.models import Policy
from ....core.models import Deployment
from ....core.serializers import PlatformSerializer
from ....core.views import ExportViewSet, MigasViewSet
from ....device.models import Driver, Logical, Model
from ....device.serializers import LogicalInfoSerializer
from ....hardware.models import Node
from ....hardware.serializers import NodeOnlySerializer
from ....mixins import DatabaseCheckMixin
from ....stats.utils import filter_computers_by_date
from ....utils import replace_keys
from ... import models, serializers
from ...filters import ComputerFilter


@extend_schema(tags=['computers'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            location=OpenApiParameter.QUERY,
            description='Fields: settings.MIGASFREE_COMPUTER_SEARCH_FIELDS, sync_user__name, sync_user__fullname',
            type=str,
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class ComputerViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = models.Computer.objects.all()
    serializer_class = serializers.ComputerSerializer
    filterset_class = ComputerFilter
    search_fields = (*settings.MIGASFREE_COMPUTER_SEARCH_FIELDS, 'sync_user__name', 'sync_user__fullname')
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

        return models.Computer.objects.scope(self.request.user.userprofile).prefetch_related(
            'tags',
            'node_set',
            'node_set__configuration_set',
        )

    def partial_update(self, request, *args, **kwargs):
        data = dict(request.data.lists()) if isinstance(request.data, QueryDict) else request.data

        devices = data.get('assigned_logical_devices_to_cid[]', data.get('assigned_logical_devices_to_cid', None))
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
                    capability=logical_device.capability, model=model, project=computer.project
                ).exists():
                    return Response(
                        {
                            'error': _(
                                'Error in capability %s for assign computer %s.'
                                ' There is no driver defined for project %s in model %s.'
                            )
                            % (logical_device.capability, computer, computer.project, model),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            computer.update_logical_devices(assigned_logical_devices_to_cid)

        return super().partial_update(request, *args, **kwargs)

    @action(methods=['get'], detail=True, url_name='devices')
    def devices(self, request, pk=None):
        computer = self.get_object()
        serializer = serializers.ComputerDevicesSerializer(computer, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def label(self, request, pk=None):
        computer = self.get_object()

        response = {
            'uuid': computer.uuid,
            'name': computer.name,
            'search': computer.__str__(),
            'helpdesk': settings.MIGASFREE_HELP_DESK,
        }

        return Response(response, status=status.HTTP_200_OK)

    @action(methods=['get', 'delete'], detail=True, url_path='software/inventory', url_name='software_inventory')
    def software_inventory(self, request, pk=None):
        """
        Returns installed packages in a computer
        """
        computer = self.get_object()

        if request.method == 'DELETE' and request.user.is_superuser:
            computer.packagehistory_set.filter(uninstall_date__isnull=True, package__project=computer.project).delete()

        data = list(
            computer.packagehistory_set.filter(uninstall_date__isnull=True, package__project=computer.project)
            .values(
                'package__id',
                'package__fullname',
            )
            .distinct()
            .order_by('package__fullname')
        )

        return Response(
            replace_keys(
                data,
                {
                    'package__id': 'id',
                    'package__fullname': 'name',
                },
            ),
            status=status.HTTP_200_OK,
        )

    @action(methods=['get', 'delete'], detail=True, url_path='software/history', url_name='software_history')
    def software_history(self, request, pk=None):
        """
        Returns software history of a computer
        """
        computer = self.get_object()

        if request.method == 'DELETE' and request.user.is_superuser:
            computer.delete_software_history(request.GET.get('key', None))

        return Response(computer.get_software_history(), status=status.HTTP_200_OK)

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
                _('Status must have one of the values: %s') % (dict(models.Computer.STATUS_CHOICES).keys())
            )

        serializer = serializers.ComputerSerializer(computer, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='status')
    def status_choices(self, request):
        response = {
            'choices': dict(models.Computer.STATUS_CHOICES),
            'productive': models.Computer.PRODUCTIVE_STATUS,
            'unproductive': models.Computer.UNPRODUCTIVE_STATUS,
            'active': models.Computer.ACTIVE_STATUS,
            'subscribed': models.Computer.SUBSCRIBED_STATUS,
            'unsubscribed': models.Computer.UNSUBSCRIBED_STATUS,
        }

        return Response(response, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def errors(self, request, pk=None):
        self.get_object()

        return Response(
            {
                'unchecked': models.Error.unchecked.filter(computer__pk=pk).count(),
                'total': models.Error.objects.filter(computer__pk=pk).count(),
            },
            status=status.HTTP_200_OK,
        )

    @action(methods=['get'], detail=True)
    def faults(self, request, pk=None):
        self.get_object()

        return Response(
            {
                'unchecked': models.Fault.unchecked.filter(computer__pk=pk).count(),
                'total': models.Fault.objects.filter(computer__pk=pk).count(),
            },
            status=status.HTTP_200_OK,
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
        target = get_object_or_404(models.Computer, id=request.data.get('target'))

        models.Computer.replacement(source, target)

        return Response(status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def synchronizing(self, request):
        result, _ = filter_computers_by_date(gt)
        sync_computers = models.Computer.objects.filter(pk__in=result)

        serializer = serializers.ComputerSerializer(sync_computers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def delayed(self, request):
        result, _ = filter_computers_by_date(le)
        delayed_computers = models.Computer.objects.filter(pk__in=result)

        serializer = serializers.ComputerSerializer(delayed_computers, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

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

        repos = Deployment.available_deployments(computer, computer.get_all_attributes()).values('id', 'name', 'source')
        definitions = models.FaultDefinition.enabled_for_attributes(computer.get_all_attributes()).values('id', 'name')

        pkgs = Deployment.available_deployments(computer, computer.get_all_attributes()).values_list(
            'packages_to_install', 'packages_to_remove', 'name', 'id'
        )

        install = set()
        remove = set()
        for install_item, remove_item, deploy_name, deploy_id in pkgs:
            if install_item:
                for pkg in install_item.split('\n'):
                    if pkg:
                        install.add(json.dumps({'package': pkg, 'name': deploy_name, 'id': deploy_id}, sort_keys=True))

            if remove_item:
                for pkg in remove_item.split('\n'):
                    if pkg:
                        remove.add(json.dumps({'package': pkg, 'name': deploy_name, 'id': deploy_id}, sort_keys=True))

        packages = {'install': [json.loads(x) for x in install], 'remove': [json.loads(x) for x in remove]}

        policy_pkg_to_install, policy_pkg_to_remove = Policy.get_packages(computer)
        policies = {'install': policy_pkg_to_install, 'remove': policy_pkg_to_remove}

        capture = computer.hardware_capture_is_required()

        logical_devices = []
        for device in computer.logical_devices():
            logical_devices.append(LogicalInfoSerializer(device).data)

        default_logical_device = computer.default_logical_device.id if computer.default_logical_device else 0

        response = {
            'deployments': repos,
            'fault_definitions': definitions,
            'packages': packages,
            'policies': policies,
            'capture_hardware': capture,
            'logical_devices': logical_devices,
            'default_logical_device': default_logical_device,
        }

        return Response(response, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def hardware(self, request, pk=None):
        computer = self.get_object()
        request.user.userprofile.check_scope(pk)

        results = Node.objects.filter(computer=computer).order_by('id', 'parent_id', 'level')

        return Response(NodeOnlySerializer(results, many=True).data, status=status.HTTP_200_OK)
