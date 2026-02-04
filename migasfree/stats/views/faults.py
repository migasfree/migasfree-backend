# Copyright (c) 2016-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2016-2026 Alberto Gacías <alberto@migasfree.org>
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
from rest_framework import permissions, status
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...client.models import Fault
from ...utils import replace_keys
from .events_project import EventProjectViewSet


@extend_schema(tags=['stats'])
@permission_classes((permissions.IsAuthenticated,))
class FaultStatsViewSet(EventProjectViewSet):
    serializer_class = None

    @action(methods=['get'], detail=False, url_path='definition')
    def by_definition(self, request):
        user = request.user.userprofile

        return Response(
            {
                'title': _('Faults / Fault Definition'),
                'total': Fault.objects.scope(user).count(),
                'data': replace_keys(
                    list(Fault.group_by_definition(user)),
                    {'fault_definition__name': 'name', 'fault_definition__id': 'fault_definition_id', 'count': 'value'},
                ),
            },
            status=status.HTTP_200_OK,
        )
