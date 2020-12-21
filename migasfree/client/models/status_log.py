# -*- coding: utf-8 *-*

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

from functools import reduce

from django.db import models
from django.db.models.aggregates import Count
from django.utils.translation import gettext_lazy as _

from .computer import Computer
from .event import Event


class DomainStatusLogManager(models.Manager):
    def scope(self, user):
        qs = super(DomainStatusLogManager, self).get_queryset()
        if not user.is_view_all():
            qs = qs.filter(computer_id__in=user.get_computers())

        return qs


class StatusLogManager(DomainStatusLogManager):
    def create(self, computer):
        obj = StatusLog()
        obj.computer = computer
        obj.status = computer.status
        obj.save()

        return obj


class StatusLog(Event):
    status = models.CharField(
        verbose_name=_('status'),
        max_length=20,
        null=False,
        choices=Computer.STATUS_CHOICES,
        default='intended'
    )

    objects = StatusLogManager()

    @staticmethod
    def by_status(user):
        total = StatusLog.objects.scope(user).count()

        data = list(StatusLog.objects.scope(user).values(
            'status',
        ).annotate(
            count=Count('id')
        ).order_by('status', '-count'))

        subscribed_sum = reduce(
            lambda x, y: x + y['count'],
            list(filter(lambda s: s['status'] != 'unsubscribed', data)),
            0
        )
        unsubscribed_sum = list(filter(lambda s: s['status'] == 'unsubscribed', data))
        unsubscribed_sum = unsubscribed_sum[0]['count'] if len(unsubscribed_sum) > 0 else 0

        inner = []
        if subscribed_sum:
            inner.append({
                'name': _('Subscribed'),
                'value': subscribed_sum,
                'status_in': 'intended,reserved,unknown,in repair,available',
            })

        if unsubscribed_sum:
            inner.append({
                'name': _('unsubscribed'),
                'value': unsubscribed_sum,
                'status_in': 'unsubscribed',
            })

        outer = []
        for item in data:
            outer.append({
                'name': _(dict(Computer.STATUS_CHOICES)[item.get('status')]),
                'value': item.get('count'),
                'status_in': item.get('status')
            })

        return {
            'total': total,
            'inner': inner,
            'outer': outer,
        }

    class Meta:
        app_label = 'client'
        verbose_name = _("Status Log")
        verbose_name_plural = _("Status Logs")
