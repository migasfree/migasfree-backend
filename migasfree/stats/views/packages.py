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

from ...core.models import Package
from ...utils import replace_keys


@extend_schema(tags=['stats'])
@permission_classes((permissions.IsAuthenticated,))
class PackageStatsViewSet(viewsets.ViewSet):
    @action(methods=['get'], detail=False, url_path='store')
    def by_store(self, request):
        data = Package.by_store(request.user.userprofile)
        inner_aliases = {
            'project__id': 'project_id',
            'project__name': 'name',
            'count': 'value'
        }
        outer_aliases = {
            'project__id': 'project_id',
            'store__id': 'store_id',
            'store__name': 'name',
            'count': 'value'
        }

        return Response(
            {
                'title': _('Packages / Store'),
                'total': data['total'],
                'inner': replace_keys(data['inner'], inner_aliases),
                'outer': replace_keys(data['outer'], outer_aliases)
            },
            status=status.HTTP_200_OK
        )
