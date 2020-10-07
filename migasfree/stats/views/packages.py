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

from collections import defaultdict

from django.db.models.aggregates import Count
from django.utils.translation import gettext as _
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...core.models import Package, Project


@permission_classes((permissions.IsAuthenticated,))
class PackageStatsViewSet(viewsets.ViewSet):
    @action(methods=['get'], detail=False, url_path='store')
    def by_store(self, request, format=None):
        user = request.user.userprofile
        total = Package.objects.scope(user).count()

        values = defaultdict(list)
        for item in Package.objects.scope(user).values(
            'project__id', 'store__id', 'store__name'
        ).annotate(
            count=Count('id')
        ).order_by('project__id', '-count'):
            values[item.get('project__id')].append(
                {
                    'name': item.get('store__name'),
                    'value': item.get('count'),
                    'project_id': item.get('project__id'),
                    'store_id': item.get('store__id')
                }
            )

        data = []
        for project in Project.objects.scope(user).all():
            if project.id in values:
                count = sum(item.get('value') for item in values[project.id])
                data.append(
                    {
                        'name': project.name,
                        'value': count,
                        'project_id': project.id,
                        'data': values[project.id]
                    }
                )

        return Response(
            {
                'title': _('Packages / Store'),
                'total': total,
                'data': data,
            },
            status=status.HTTP_200_OK
        )
