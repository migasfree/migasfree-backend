# -*- coding: utf-8 -*-

# Copyright (c) 2015 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015 Alberto Gacías <alberto@migasfree.org>
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

from __future__ import absolute_import

from django.db.models import Q
from celery import shared_task
from celery.exceptions import Ignore
from django_redis import get_redis_connection
from rest_framework.reverse import reverse

from migasfree.core.models import Package, Release
from migasfree.client.models import Notification, Fault, Error, Computer

from ..utils import trans as _

import logging
logger = logging.getLogger('celery')


def add_orphaned_packages(con):
    con.hmset(
        'migasfree:chk:orphaned', {
            'msg': _('Orphaned Package/Set'),
            'target': 'server',
            'level': 'warning',
            'result': Package.orphaned(),
            'api': reverse('package-orphaned'),
        }
    )
    con.sadd('migasfree:watch:chk', 'orphaned')


def add_unchecked_notifications(con):
    con.hmset(
        'migasfree:chk:notifications', {
            'msg': _('Unchecked Notifications'),
            'target': 'server',
            'level': 'warning',
            'result': Notification.unchecked(),
            'api': '%s?checked=False' % reverse('notification-list')
        }
    )
    con.sadd('migasfree:watch:chk', 'notifications')


def add_unchecked_faults(con):
    con.hmset(
        'migasfree:chk:faults', {
            'msg': _('Unchecked Faults'),
            'target': 'computer',
            'level': 'critical',
            'result': Fault.unchecked(),
            'api': '%s?checked=False' % reverse('fault-list')
        }
    )
    con.sadd('migasfree:watch:chk', 'faults')


def add_unchecked_errors(con):
    con.hmset(
        'migasfree:chk:errors', {
            'msg': _('Unchecked Errors'),
            'target': 'computer',
            'level': 'critical',
            'result': Error.unchecked(),
            'api': '%s?checked=False' % reverse('error-list')
        }
    )
    con.sadd('migasfree:watch:chk', 'errors')


def add_generating_repos(con):
    result = con.scard('migasfree:watch:repos')
    con.hmset(
        'migasfree:chk:repos', {
            'msg': _('Generating Repositories'),
            'target': 'server',
            'level': 'info',
            'result': result,
            'api': '/api/v1/token/repos/generating/'  # TODO??? reverse
        }
    )
    con.sadd('migasfree:watch:chk', 'repos')


@shared_task(queue='default')
def alerts():
    con = get_redis_connection('default')

    add_orphaned_packages(con)
    add_unchecked_notifications(con)
    add_unchecked_faults(con)
    add_unchecked_errors(con)
    add_generating_repos(con)
    # add_synchronizing_computers(con)
    # add_delayed_computers(con)

    logger.debug(con.smembers('migasfree:watch:chk'))


def assigned_computers_to_release(release_id):
    try:
        release = Release.objects.get(pk=release_id)
    except:
        return

    computers = set(Computer.objects.filter(
        Q(project=release.project) & (
            Q(sync_attributes__id__in=release.included_attributes.all())
            | Q(tags__id__in=release.included_attributes.all())
        )
    ).values_list('id', flat=True))

    if release.schedule and release.schedule.scheduledelay_set:
        for delay in release.schedule.scheduledelay_set.all():
            computers = computers.union(set(Computer.objects.filter(
                Q(project=release.project) & (
                    Q(sync_attributes__id__in=delay.attributes.all())
                    | Q(tags__id__in=delay.attributes.all())
                )
            ).values_list('id', flat=True)))

    computers = computers.difference(set(Computer.objects.filter(
        Q(project=release.project) & (
            Q(sync_attributes__id__in=release.excluded_attributes.all())
            | Q(tags__id__in=release.excluded_attributes.all())
        )
    ).values_list('id', flat=True)))

    con = get_redis_connection('default')
    key = 'migasfree:releases:%d:computers' % release_id
    con.delete(key)
    if computers:
        [con.sadd(key, computer_id) for computer_id in list(computers)]


@shared_task(queue='default')
def computers_releases():
    for release in Release.objects.all():
        assigned_computers_to_release(release.id)
