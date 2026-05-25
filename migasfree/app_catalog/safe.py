# Copyright (c) 2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2026 Alberto Gacías <alberto@migasfree.org>
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

import logging

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ..client.models import Computer
from ..core.mixins import SafeConnectionMixin
from . import models, serializers

logger = logging.getLogger('migasfree')


@extend_schema(tags=['safe'])
@permission_classes((permissions.AllowAny,))
class SafeCategoryViewSet(SafeConnectionMixin, viewsets.ViewSet):
    @extend_schema(
        description='Returns software catalog categories (requires mTLS)',
        responses={
            status.HTTP_200_OK: serializers.CategorySerializer(many=True),
            status.HTTP_400_BAD_REQUEST: {'description': 'Error in request'},
        },
    )
    def create(self, request):
        claims = self.get_claims(request.data)
        if isinstance(claims, str):
            return Response(self.create_response(claims), status=status.HTTP_400_BAD_REQUEST)

        results = models.Category.objects.all().order_by('name')
        serializer = serializers.CategorySerializer(results, many=True)

        return Response(self.create_response(serializer.data), status=status.HTTP_200_OK)


@extend_schema(tags=['safe'])
@permission_classes((permissions.AllowAny,))
class SafeApplicationViewSet(SafeConnectionMixin, viewsets.ViewSet):
    @extend_schema(
        description='Returns available applications for a given computer (requires mTLS)',
        responses={
            status.HTTP_200_OK: serializers.ApplicationSerializer(many=True),
            status.HTTP_400_BAD_REQUEST: {'description': 'Error in request'},
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
    )
    @action(methods=['post'], detail=False)
    def available(self, request):
        claims = self.get_claims(request.data)
        if isinstance(claims, str):
            return Response(self.create_response(claims), status=status.HTTP_400_BAD_REQUEST)

        if not claims or 'cid' not in claims:
            return Response(self.create_response(_('Malformed claims')), status=status.HTTP_400_BAD_REQUEST)

        computer = get_object_or_404(Computer, pk=claims.get('cid'))
        category = claims.get('category', 0)
        level = claims.get('level', '')
        query = claims.get('q', '')

        results = (
            models.Application.objects.select_related('category')
            .prefetch_related(
                'available_for_attributes',
                'packages_by_project__project',
            )
            .filter(
                available_for_attributes__in=computer.sync_attributes.values_list('id', flat=True),
                packages_by_project__project=computer.project,
            )
            .order_by('-score', 'name')
            .distinct()
        )

        if category:
            results = results.filter(category=category)
        if level:
            results = results.filter(level=level)
        if query:
            results = results.filter(Q(name__icontains=query) | Q(description__icontains=query))

        serializer = serializers.ApplicationSerializer(results, many=True)
        return Response(self.create_response(serializer.data), status=status.HTTP_200_OK)
