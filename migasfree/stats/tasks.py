# -*- coding: utf-8 -*-

# Copyright (c) 2015-2017 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2017 Alberto Gacías <alberto@migasfree.org>
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

from datetime import datetime, timedelta

from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.utils.translation import ugettext
from celery import shared_task
from django_redis import get_redis_connection
from rest_framework.reverse import reverse

from migasfree.core.models import Package, Deployment
from migasfree.client.models import Notification, Fault, Error, Computer

import logging
logger = logging.getLogger('celery')


def add_orphan_packages():
    con = get_redis_connection()
    con.hmset(
        'migasfree:chk:orphan', {
            'msg': ugettext('Orphan Package/Set'),
            'target': 'server',
            'level': 'warning',
            'result': Package.orphan(),
            'api': reverse('package-orphan'),
        }
    )
    con.sadd('migasfree:watch:chk', 'orphan')


def add_unchecked_notifications():
    con = get_redis_connection()
    con.hmset(
        'migasfree:chk:notifications', {
            'msg': ugettext('Unchecked Notifications'),
            'target': 'server',
            'level': 'warning',
            'result': Notification.unchecked_count(),
            'api': '%s?checked=False' % reverse('notification-list')
        }
    )
    con.sadd('migasfree:watch:chk', 'notifications')


def add_unchecked_faults():
    con = get_redis_connection()
    con.hmset(
        'migasfree:chk:faults', {
            'msg': ugettext('Unchecked Faults'),
            'target': 'computer',
            'level': 'critical',
            'result': Fault.unchecked_count(),
            'api': '%s?checked=False' % reverse('fault-list')
        }
    )
    con.sadd('migasfree:watch:chk', 'faults')


def add_unchecked_errors():
    con = get_redis_connection()
    con.hmset(
        'migasfree:chk:errors', {
            'msg': ugettext('Unchecked Errors'),
            'target': 'computer',
            'level': 'critical',
            'result': Error.unchecked_count(),
            'api': '%s?checked=False' % reverse('error-list')
        }
    )
    con.sadd('migasfree:watch:chk', 'errors')


def add_generating_repos():
    con = get_redis_connection()
    result = con.scard('migasfree:watch:repos')
    con.hmset(
        'migasfree:chk:repos', {
            'msg': ugettext('Generating Repositories'),
            'target': 'server',
            'level': 'info',
            'result': result,
            'api': reverse('deployment-generating')
        }
    )
    con.sadd('migasfree:watch:chk', 'repos')


def add_synchronizing_computers():
    con = get_redis_connection()

    result = 0
    delayed_time = datetime.now() - timedelta(
        seconds=settings.MIGASFREE_SECONDS_MESSAGE_ALERT
    )

    computers = con.smembers('migasfree:watch:msg')
    for computer_id in computers:
        date = con.hget('migasfree:msg:%s' % computer_id, 'date')
        if datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f') > delayed_time:
            result += 1

    con.hmset(
        'migasfree:chk:syncs', {
            'msg': ugettext('Synchronizing Computers Now'),
            'target': 'computer',
            'level': 'info',
            'result': result,
            'api': reverse('computer-synchronizing')
        }
    )
    con.sadd('migasfree:watch:chk', 'syncs')


def add_delayed_computers():
    con = get_redis_connection()

    result = 0
    delayed_time = datetime.now() - timedelta(
        seconds=settings.MIGASFREE_SECONDS_MESSAGE_ALERT
    )

    computers = con.smembers('migasfree:watch:msg')
    for computer_id in computers:
        date = con.hget('migasfree:msg:%s' % computer_id, 'date')
        if datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f') <= delayed_time:
            result += 1

    con.hmset(
        'migasfree:chk:delayed', {
            'msg': ugettext('Delayed Computers'),
            'target': 'computer',
            'level': 'critical',
            'result': result,
            'api': reverse('computer-delayed')
        }
    )
    con.sadd('migasfree:watch:chk', 'delayed')


@shared_task(queue='default')
def alerts():
    con = get_redis_connection()

    add_orphan_packages()
    add_unchecked_notifications()
    add_unchecked_faults()
    add_unchecked_errors()
    add_generating_repos()
    add_synchronizing_computers()
    add_delayed_computers()

    logger.debug(con.smembers('migasfree:watch:chk'))


def assigned_computers_to_deployment(deployment_id):
    try:
        deploy = Deployment.objects.get(pk=deployment_id)
    except ObjectDoesNotExist:
        return

    computers = set(Computer.objects.filter(
        Q(project=deploy.project) & (
            Q(sync_attributes__id__in=deploy.included_attributes.all())
            | Q(tags__id__in=deploy.included_attributes.all())
        )
    ).values_list('id', flat=True))

    if deploy.schedule and deploy.schedule.delays:
        for delay in deploy.schedule.delays.all():
            computers = computers.union(set(Computer.objects.filter(
                Q(project=deploy.project) & (
                    Q(sync_attributes__id__in=delay.attributes.all())
                    | Q(tags__id__in=delay.attributes.all())
                )
            ).values_list('id', flat=True)))

    computers = computers.difference(set(Computer.objects.filter(
        Q(project=deploy.project) & (
            Q(sync_attributes__id__in=deploy.excluded_attributes.all())
            | Q(tags__id__in=deploy.excluded_attributes.all())
        )
    ).values_list('id', flat=True)))

    con = get_redis_connection()
    key = 'migasfree:deployments:%d:computers' % deployment_id
    con.delete(key)
    if computers:
        [con.sadd(key, computer_id) for computer_id in list(computers)]


@shared_task(queue='default')
def computers_deployments():
    for deploy in Deployment.objects.all():
        assigned_computers_to_deployment(deploy.id)
