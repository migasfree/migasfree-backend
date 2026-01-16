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

from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import permission_classes

from ....core.views import ExportViewSet, MigasViewSet
from ....mixins import DatabaseCheckMixin
from ... import models, serializers
from ...filters import MigrationFilter


@extend_schema(tags=['migrations'])
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search', location=OpenApiParameter.QUERY, description='Fields: computer__name, computer__id', type=str
        )
    ],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class MigrationViewSet(
    DatabaseCheckMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
    MigasViewSet,
    ExportViewSet,
):
    queryset = models.Migration.objects.all()
    serializer_class = serializers.MigrationSerializer
    filterset_class = MigrationFilter
    search_fields = ('computer__name', 'computer__id')
    ordering_fields = '__all__'
    ordering = ('-created_at',)

    def get_queryset(self):
        if self.request is None:
            return models.Migration.objects.none()

        return models.Migration.objects.scope(self.request.user.userprofile)
