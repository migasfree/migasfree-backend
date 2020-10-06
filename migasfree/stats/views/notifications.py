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

from django.utils.translation import gettext as _
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...client.models import Notification

from .events import event_by_month, month_interval


@permission_classes((permissions.IsAuthenticated,))
class NotificationStatsViewSet(viewsets.ViewSet):
    @action(methods=['get'], detail=False, url_path='month')
    def by_month(self, request, format=None):
        begin_date, end_date = month_interval()

        data = event_by_month(
            Notification.stacked_by_month(begin_date),
            begin_date,
            end_date,
            'notification',
            field='checked'
        )
        return Response(
            data,
            status=status.HTTP_200_OK
        )
