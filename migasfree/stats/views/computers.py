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

from django.db.models import Count
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext as _
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from ...client.models import Computer
from ...utils import replace_keys

from .events import event_by_month, month_interval


@permission_classes((permissions.IsAuthenticated,))
class ComputerStatsViewSet(viewsets.ViewSet):
    @action(methods=['get'], detail=False)
    def projects(self, request, format=None):
        return Response(
            replace_keys(
                list(Computer.group_by_project()),
                {
                    'project__name': 'name',
                    'project__id': 'project_id',
                    'count': 'value'
                }
            ),
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False)
    def platforms(self, request, format=None):
        return Response(
            replace_keys(
                list(Computer.group_by_platform()),
                {
                    'project__platform__name': 'name',
                    'project__platform__id': 'platform_id',
                    'count': 'value'
                }
            ),
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='machine')
    def by_machine(self, request, format=None):
        total = Computer.objects.scope(request.user.userprofile).count()
        link = '{}?_REPLACE_'.format(
            reverse('admin:client_computer_changelist')
        )

        data = {
            'inner': [],
            'outer': [],
        }

        count_subscribed = Computer.subscribed.scope(request.user.userprofile).count()
        count_subscribed_virtual = Computer.subscribed.scope(request.user.userprofile).filter(machine='V').count()
        count_subscribed_physical = Computer.subscribed.scope(request.user.userprofile).filter(machine='P').count()
        count_unsubscribed = Computer.unsubscribed.scope(request.user.userprofile).count()
        count_unsubscribed_virtual = Computer.unsubscribed.scope(request.user.userprofile).filter(machine='V').count()
        count_unsubscribed_physical = Computer.unsubscribed.scope(request.user.userprofile).filter(machine='P').count()

        if count_subscribed:
            if count_subscribed_virtual:
                data['outer'].append(
                    {
                        'name': _('Virtual'),
                        'value': count_subscribed_virtual,
                        'url': link.replace(
                            '_REPLACE_',
                            'status__in=intended,reserved,unknown,available,in repair&machine__exact=V'
                        )
                    }
                )

            if count_subscribed_physical:
                data['outer'].append(
                    {
                        'name': _('Physical'),
                        'value': count_subscribed_physical,
                        'url': link.replace(
                            '_REPLACE_',
                            'status__in=intended,reserved,unknown,available,in repair&machine__exact=P'
                        )
                    }
                )

            data['inner'].append(
                {
                    'name': _('Subscribed'),
                    'value': count_subscribed,
                    'url': link.replace(
                        '_REPLACE_',
                        'status__in=intended,reserved,unknown,available,in repair'
                    ),
                },
            )

        if count_unsubscribed:
            if count_unsubscribed_virtual:
                data['outer'].append(
                    {
                        'name': _('Virtual'),
                        'value': count_unsubscribed_virtual,
                        'url': link.replace(
                            '_REPLACE_',
                            'status__in=unsubscribed&machine__exact=V'
                        )
                    }
                )

            if count_unsubscribed_physical:
                data['outer'].append(
                    {
                        'name': _('Physical'),
                        'value': count_unsubscribed_physical,
                        'url': link.replace(
                            '_REPLACE_',
                            'status__in=unsubscribed&machine__exact=P'
                        )
                    }
                )

            data['inner'].append(
                {
                    'name': _('Unsubscribed'),
                    'value': count_unsubscribed,
                    'url': link.replace(
                        '_REPLACE_',
                        'status__in=unsubscribed'
                    ),
                }
            )

        return Response(
            {
                'title': _('Computers / Machine'),
                'total': total,
                'inner': data['inner'],
                'outer': data['outer'],
                'url': link.replace('?_REPLACE_', ''),
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='status')
    def by_status(self, request, format=None):
        # TODO response format (inner, outer)
        total = Computer.objects.scope(request.user.userprofile).exclude(status='unsubscribed').count()
        link = '{}?_REPLACE_'.format(
            reverse('admin:client_computer_changelist')
        )

        values = dict()
        for item in Computer.objects.scope(
            request.user.userprofile
        ).exclude(
            status='unsubscribed'
        ).values(
            'status'
        ).annotate(
            count=Count('id')
        ).order_by('status', '-count'):
            status_name = _(dict(Computer.STATUS_CHOICES)[item.get('status')])
            values[item.get('status')] = {
                'name': status_name,
                'value': item.get('count'),
                'url': link.replace(
                    '_REPLACE_',
                    'status__in={}'.format(item.get('status'))
                ),
            }

        count_productive = values.get('intended', {}).get('value', 0) \
            + values.get('reserved', {}).get('value', 0) \
            + values.get('unknown', {}).get('value', 0)
        data_productive = []
        if 'intended' in values:
            data_productive.append(values['intended'])
        if 'reserved' in values:
            data_productive.append(values['reserved'])
        if 'unknown' in values:
            data_productive.append(values['unknown'])

        count_unproductive = values.get('available', {}).get('value', 0) \
            + values.get('in repair', {}).get('value', 0)
        data_unproductive = []
        if 'available' in values:
            data_unproductive.append(values['available'])
        if 'in repair' in values:
            data_unproductive.append(values['in repair'])

        data = [
            {
                'name': _('Productive'),
                'value': count_productive,
                'url': link.replace(
                    '_REPLACE_',
                    'status__in=intended,reserved,unknown'
                ),
                'data': data_productive,
            },
            {
                'name': _('Unproductive'),
                'value': count_unproductive,
                'url': link.replace(
                    '_REPLACE_',
                    'status__in=available,in repair'
                ),
                'data': data_unproductive,
            },
        ]

        return Response(
            {
                'title': _('Subscribed Computers / Status'),
                'total': total,
                'data': data,
                'url': link.replace('_REPLACE_', 'status__in=intended,reserved,unknown,available,in repair'),
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='attributes/count')
    def attributes_count(self, request, format=None):
        attributes = request.query_params.getlist('attributes')
        project_id = request.query_params.get('project_id', None)

        return Response(
            Computer.count_by_attributes(attributes, project_id),
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='new/month')
    def new_by_month(self, request, format=None):
        begin_date, end_date = month_interval()

        data = event_by_month(
            Computer.stacked_by_month(request.user.userprofile, begin_date),
            begin_date,
            end_date,
            'computer'
        )
        return Response(
            data,
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='productive/platform')
    def productive_by_platform(self, request, format=None):
        data = Computer.productive_computers_by_platform(request.user.userprofile)
        inner_aliases = {
            'project__platform__id': 'platform_id',
            'project__platform__name': 'name',
            'count': 'value'
        }
        outer_aliases = {
            'project__name': 'name',
            'project__id': 'project_id',
            'project__platform__id': 'platform_id',
            'count': 'value'
        }

        return Response(
            {
                'total': data['total'],
                'inner': replace_keys(data['inner'], inner_aliases),
                'outer': replace_keys(data['outer'], outer_aliases)
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='entry/year')
    def entry_year(self, request, format=None):
        url = '{}?machine__exact=P&_REPLACE_'.format(
            reverse('admin:client_computer_changelist')
        )
        results = Computer.entry_year(request.user.userprofile)
        data = [x['count'] for x in results]
        labels = [x['year'] for x in results]

        for i, item in enumerate(labels):
            querystring = {
                'created_at__gte': '{}-01-01'.format(labels[i]),
                'created_at__lt': '{}-01-01'.format(labels[i] + 1)
            }
            data[i] = {
                'value': data[i],
                'url': url.replace(
                    '_REPLACE_',
                    urlencode(querystring)
                )
            }

        return Response(
            {
                'x_labels': labels,
                'data': {_('Computers'): data}
            },
            status=status.HTTP_200_OK
        )
