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

from django.db.models import Count
from django.utils.translation import gettext as _
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...core.models import ClientAttribute, ServerAttribute


@permission_classes((permissions.IsAuthenticated,))
class ClientAttributeStatsViewSet(viewsets.ViewSet):
    @action(methods=['get'], detail=False, url_path='property')
    def by_property(self, request):
        total = ClientAttribute.objects.scope(request.user.userprofile).count()

        data = []
        for item in ClientAttribute.objects.scope(request.user.userprofile).values(
            'property_att__id', 'property_att__name'
        ).annotate(
            count=Count('property_att__id')
        ).order_by('-count'):
            data.append({
                'name': item.get('property_att__name'),
                'value': item.get('count'),
                'property_att_id': item.get('property_att__id'),
            })

        return Response(
            {
                'title': _('Attributes / Formula'),
                'total': total,
                'data': data,
            },
            status=status.HTTP_200_OK
        )


@permission_classes((permissions.IsAuthenticated,))
class ServerAttributeStatsViewSet(viewsets.ViewSet):
    @action(methods=['get'], detail=False, url_path='category')
    def by_category(self, request):
        total = ServerAttribute.objects.scope(request.user.userprofile).count()

        data = []
        for item in ServerAttribute.objects.scope(request.user.userprofile).values(
            'property_att__id', 'property_att__name'
        ).annotate(
            count=Count('property_att__id')
        ).order_by('-count'):
            data.append({
                'name': item.get('property_att__name'),
                'value': item.get('count'),
                'property_att_id': item.get('property_att__id'),
            })

        return Response(
            {
                'title': _('Tags / Tag Category'),
                'total': total,
                'data': data,
            },
            status=status.HTTP_200_OK
        )
