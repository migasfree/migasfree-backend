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

from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...utils import replace_keys
from ...device.models import Device, Model


@extend_schema(tags=['stats'])
@permission_classes((permissions.IsAuthenticated,))
class DeviceStatsViewSet(viewsets.ViewSet):
    @action(methods=['get'], detail=False, url_path='connection')
    def by_connection(self, request):
        return Response(
            {
                'title': _('Devices / Connection'),
                'total': Device.objects.count(),
                'data': replace_keys(
                    list(Device.group_by_connection()),
                    {
                        'connection__name': 'name',
                        'connection__id': 'connection_id',
                        'count': 'value'
                    }
                ),
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='model')
    def by_model(self, request):
        return Response(
            {
                'title': _('Devices / Model'),
                'total': Device.objects.count(),
                'data': replace_keys(
                    list(Device.group_by_model()),
                    {
                        'model__name': 'name',
                        'model__id': 'model_id',
                        'count': 'value'
                    }
                ),
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='manufacturer')
    def by_manufacturer(self, request):
        return Response(
            {
                'title': _('Devices / Manufacturer'),
                'total': Device.objects.count(),
                'data': replace_keys(
                    list(Device.group_by_manufacturer()),
                    {
                        'model__manufacturer__name': 'name',
                        'model__manufacturer__id': 'manufacturer_id',
                        'count': 'value'
                    }
                ),
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='models/manufacturer')
    def models_by_manufacturer(self, request):
        return Response(
            {
                'title': _('Models / Manufacturer'),
                'total': Model.objects.count(),
                'data': replace_keys(
                    list(Model.group_by_manufacturer()),
                    {
                        'manufacturer__name': 'name',
                        'manufacturer__id': 'manufacturer_id',
                        'count': 'value'
                    }
                ),
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='models/project')
    def models_by_project(self, request):
        total = Model.objects.count()

        x_axe = []
        data = []
        for item in Model.group_by_project():
            x_axe.append(item['drivers__project__name'])
            data.append({
                'value': item['count'],
                'drivers__project__id': item['drivers__project__id']
            })

        return Response(
            {'x_labels': x_axe, 'data': data, 'total': total},
            status=status.HTTP_200_OK
        )
