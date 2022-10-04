# -*- coding: UTF-8 -*-

# Copyright (c) 2020-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2020-2021 Alberto Gacías <alberto@migasfree.org>
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

from rest_framework.response import Response
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import permission_classes

from ..tasks import get_alerts
from ...mixins import DatabaseCheckMixin


@permission_classes((permissions.IsAuthenticated,))
class AlertsViewSet(DatabaseCheckMixin, viewsets.ViewSet):
    def list(self, request):
        return Response(get_alerts(), status=status.HTTP_200_OK)
