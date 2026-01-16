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

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from ....app_catalog.resources import (
    ApplicationResource,
    CategoryResource,
    PolicyResource,
)
from ....client.resources import (
    ComputerResource,
    ErrorResource,
    FaultDefinitionResource,
    FaultResource,
    MigrationResource,
    NotificationResource,
    PackageHistoryResource,
    StatusLogResource,
    SynchronizationResource,
    UserResource,
)
from ....device.resources import (
    CapabilityResource,
    ConnectionResource,
    DeviceResource,
    DriverResource,
    LogicalResource,
    ManufacturerResource,
    ModelResource,
    TypeResource,
)
from ...resources import (
    AttributeSetResource,
    ClientAttributeResource,
    ClientPropertyResource,
    DeploymentResource,
    DomainResource,
    GroupResource,
    PackageResource,
    PackageSetResource,
    PlatformResource,
    ProjectResource,
    ScheduleResource,
    ScopeResource,
    ServerAttributeResource,
    ServerPropertyResource,
    StoreResource,
    UserProfileResource,
)


class ExportViewSet(viewsets.ViewSet):
    @action(methods=['get', 'post'], detail=False)
    def export(self, request):
        resources = {
            # app_catalog
            'application': ApplicationResource,
            'category': CategoryResource,
            'policy': PolicyResource,
            # client
            'computer': ComputerResource,
            'error': ErrorResource,
            'fault': FaultResource,
            'faultdefinition': FaultDefinitionResource,
            'migration': MigrationResource,
            'notification': NotificationResource,
            'packagehistory': PackageHistoryResource,
            'statuslog': StatusLogResource,
            'synchronization': SynchronizationResource,
            'user': UserResource,
            # core
            'attributeset': AttributeSetResource,
            'clientattribute': ClientAttributeResource,
            'clientproperty': ClientPropertyResource,
            'deployment': DeploymentResource,
            'domain': DomainResource,
            'group': GroupResource,
            'package': PackageResource,
            'packageset': PackageSetResource,
            'platform': PlatformResource,
            'project': ProjectResource,
            'schedule': ScheduleResource,
            'scope': ScopeResource,
            'serverattribute': ServerAttributeResource,
            'serverproperty': ServerPropertyResource,
            'store': StoreResource,
            'userprofile': UserProfileResource,
            # device
            'capability': CapabilityResource,
            'connection': ConnectionResource,
            'device': DeviceResource,
            'driver': DriverResource,
            'manufacturer': ManufacturerResource,
            'model': ModelResource,
            'logical': LogicalResource,
            'type': TypeResource,
        }

        class_name = self.basename
        if class_name not in resources:
            raise NotFound(f'Export not supported for {class_name}')

        if request.method == 'POST':
            new_params = request.GET.copy()
            new_params.update(request.data)
            request._request.GET = new_params

        resource = resources[class_name]()
        data = resource.export(self.filter_queryset(self.get_queryset()))

        response = HttpResponse(
            data.csv,
            status=status.HTTP_200_OK,
            content_type='text/csv',
        )
        response['Content-Disposition'] = f'attachment; filename="{self.basename}.csv"'

        return response


class MigasViewSet(viewsets.ViewSet):
    @action(methods=['get'], detail=True)
    def relations(self, request, pk=None):
        app = self.queryset.model._meta.app_label
        model = self.queryset.model._meta.model_name

        try:
            response = apps.get_model(app, model).objects.get(pk=pk).relations(request)

            return Response(response, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @action(methods=['get'], detail=True)
    def badge(self, request, pk=None):
        app = self.queryset.model._meta.app_label
        model = self.queryset.model._meta.model_name

        try:
            response = apps.get_model(app, model).objects.get(pk=pk).badge()

            return Response(response, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @action(methods=['post'], detail=False, url_path='filter')
    def filter_list(self, request, *args, **kwargs):
        """
        Generic endpoint to list with filters via POST.
        Allows to bypass the URL length limit for large filters (e.g: id__in).
        """
        new_params = request.GET.copy()
        new_params.update(request.data)
        request._request.GET = new_params

        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
