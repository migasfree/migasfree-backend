# -*- coding: UTF-8 -*-

# Copyright (c) 2015-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2021 Alberto Gacías <alberto@migasfree.org>
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
from rest_framework import status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...client.models import StatusLog

from .events import event_by_month, month_interval, EventViewSet


@permission_classes((permissions.IsAuthenticated,))
class StatusLogStatsViewSet(EventViewSet):
    @action(methods=['get'], detail=False, url_path='status')
    def by_status(self, request):
        data = StatusLog.by_status(request.user.userprofile)

        return Response(
            {
                'title': _('Status Logs / Status'),
                'total': data['total'],
                'inner': data['inner'],
                'outer': data['outer']
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='month')
    def status_by_month(self, request):
        begin_date, end_date = month_interval()

        data = event_by_month(
            StatusLog.stacked_by_month(
                request.user.userprofile, begin_date, field='status'
            ),
            begin_date,
            end_date,
            'statuslog',
            field='status'
        )
        return Response(
            data,
            status=status.HTTP_200_OK
        )
