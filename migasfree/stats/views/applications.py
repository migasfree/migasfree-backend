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

from django.db.models.aggregates import Count
from django.utils.translation import gettext as _
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...app_catalog.models import Application


@permission_classes((permissions.IsAuthenticated,))
class ApplicationStatsViewSet(viewsets.ViewSet):
    @action(methods=['get'], detail=False, url_path='category')
    def by_category(self, request, format=None):
        total = Application.objects.count()

        data = []
        for item in Application.objects.values(
            'category',
        ).annotate(
            count=Count('category')
        ).order_by('-count'):
            data.append({
                'name': '{}'.format(dict(Application.CATEGORIES)[item.get('category')]),
                'value': item.get('count'),
                'category': item.get('category')
            })

        return Response(
            {
                'title': _('Applications / Category'),
                'total': total,
                'data': data,
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='level')
    def by_level(self, request, format=None):
        total = Application.objects.count()

        data = []
        for item in Application.objects.values(
            'level',
        ).annotate(
            count=Count('level')
        ).order_by('-count'):
            data.append({
                'name': '{}'.format(dict(Application.LEVELS)[item.get('level')]),
                'value': item.get('count'),
                'level': item.get('level')
            })

        return Response(
            {
                'title': _('Applications / Level'),
                'total': total,
                'data': data,
            },
            status=status.HTTP_200_OK
        )
