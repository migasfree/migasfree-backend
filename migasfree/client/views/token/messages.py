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

import csv

from django.core.paginator import Paginator
from django.http import HttpResponse
from django_redis import get_redis_connection
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.utils.urls import remove_query_param, replace_query_param

from ....paginations import DefaultPagination
from ....utils import decode_dict
from ...messages import remove_computer_messages


@extend_schema(tags=['messages'])
@permission_classes((permissions.IsAuthenticated,))
class MessageViewSet(viewsets.ViewSet):
    serializer_class = None

    def get_queryset(self):
        id_filter = self.request.query_params.get('id__in', None)
        if id_filter:
            id_filter = list(map(int, id_filter.split(',')))
        project_filter = self.request.query_params.get('project__id', None)
        created_at_lt_filter = self.request.query_params.get('created_at__lt', None)
        created_at_gte_filter = self.request.query_params.get('created_at__gte', None)
        status_filter = self.request.query_params.get('computer__status__in', None)
        search_filter = self.request.query_params.get('search', None)

        con = get_redis_connection()
        items = list(con.smembers('migasfree:watch:msg'))

        projects = []
        computers = []
        user = self.request.user.userprofile
        if user and not user.is_view_all():
            projects = user.get_projects()
            computers = user.get_computers()

        results = []
        for key in items:
            item = decode_dict(con.hgetall(f'migasfree:msg:{int(key)}'))

            if projects and int(item['project_id']) not in projects:
                continue

            if computers and int(item['computer_id']) not in computers:
                continue

            if id_filter and int(key) not in id_filter:
                continue

            if project_filter and int(item['project_id']) != project_filter:
                continue

            if created_at_lt_filter and item['date'] >= created_at_lt_filter:
                continue

            if created_at_gte_filter and item['date'] < created_at_gte_filter:
                continue

            if status_filter and item['computer_status'] not in status_filter:
                continue

            if search_filter and search_filter.lower() not in item['msg'].lower():
                continue

            results.append(
                {
                    'id': int(key),
                    'created_at': item['date'],
                    'computer': {
                        'id': int(item['computer_id']),
                        '__str__': item['computer_name'],
                        'status': item['computer_status'],
                        'summary': item['computer_summary'],
                    },
                    'project': {'id': int(item['project_id']), 'name': item['project_name']},
                    'user': {'id': int(item['user_id']), 'name': item['user_name']},
                    'message': item['msg'],
                }
            )

        return sorted(results, key=lambda d: d['created_at'], reverse=True)

    def _get_next_link(self, request, page):
        if not page.has_next():
            return None

        url = request.build_absolute_uri()
        page_number = page.next_page_number()

        return replace_query_param(url, 'page', page_number)

    def _get_previous_link(self, request, page):
        if not page.has_previous():
            return None

        url = self.request.build_absolute_uri()
        page_number = page.previous_page_number()
        if page_number == 1:
            return remove_query_param(url, 'page')

        return replace_query_param(url, 'page', page_number)

    def list(self, request):
        results = self.get_queryset()

        paginator = Paginator(results, request.GET.get('page_size', DefaultPagination.page_size))
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        return Response(
            {
                'results': page_obj.object_list,
                'count': len(results),
                'next': self._get_next_link(request, page_obj),
                'previous': self._get_previous_link(request, page_obj),
            }
        )

    def destroy(self, request, pk=None):
        remove_computer_messages(int(pk))

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=False)
    def export(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="messages.csv"'

        writer = csv.DictWriter(
            response,
            fieldnames=[
                'created_at',
                'computer__id',
                'computer____str__',
                'computer__status',
                'computer__summary',
                'project__id',
                'project__name',
                'user__id',
                'user__name',
                'message',
            ],
        )
        writer.writeheader()

        for item in self.get_queryset():
            writer.writerow(
                {
                    'created_at': item['created_at'],
                    'computer__id': item['computer']['id'],
                    'computer____str__': item['computer']['__str__'],
                    'computer__status': item['computer']['status'],
                    'computer__summary': item['computer']['summary'],
                    'project__id': item['project']['id'],
                    'project__name': item['project']['name'],
                    'user__id': item['user']['id'],
                    'user__name': item['user']['name'],
                    'message': item['message'],
                }
            )

        return response
