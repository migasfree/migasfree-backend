# -*- coding: utf-8 -*-

# Copyright (c) 2017 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2017 Alberto Gacías <alberto@migasfree.org>
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

from rest_framework import viewsets, mixins, filters
from rest_framework_filters import backends

from migasfree.core.permissions import PublicPermission
from . import models, serializers
from .filters import ApplicationFilter


class ApplicationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = models.Application.objects.all()
    serializer_class = serializers.ApplicationSerializer
    filter_class = ApplicationFilter
    filter_backends = (filters.OrderingFilter, backends.DjangoFilterBackend)
    permission_classes = (PublicPermission,)
