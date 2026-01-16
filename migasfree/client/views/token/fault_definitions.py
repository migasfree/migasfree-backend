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

from django.db.models import Prefetch
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, viewsets
from rest_framework.decorators import permission_classes

from ....core.models import Attribute
from ....core.views import ExportViewSet, MigasViewSet
from ....mixins import DatabaseCheckMixin
from ... import models, serializers
from ...filters import FaultDefinitionFilter


@extend_schema(tags=['fault-definitions'])
@extend_schema(
    parameters=[OpenApiParameter(name='search', location=OpenApiParameter.QUERY, description='Fields: name', type=str)],
    methods=['GET'],
)
@permission_classes((permissions.DjangoModelPermissions,))
class FaultDefinitionViewSet(DatabaseCheckMixin, viewsets.ModelViewSet, MigasViewSet, ExportViewSet):
    queryset = models.FaultDefinition.objects.all()
    serializer_class = serializers.FaultDefinitionSerializer
    filterset_class = FaultDefinitionFilter
    search_fields = ('name',)
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

        return models.FaultDefinition.objects.scope(self.request.user.userprofile).prefetch_related(
            Prefetch('included_attributes', queryset=qs),
            Prefetch('excluded_attributes', queryset=qs),
            'included_attributes__property_att',
            'excluded_attributes__property_att',
            'users',
        )
