# -*- coding: utf-8 -*-

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

from __future__ import absolute_import

from datetime import datetime, timedelta

from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.utils.translation import gettext
from celery import shared_task
from django_redis import get_redis_connection
from rest_framework.reverse import reverse

from ..core.models import Package, Deployment
from ..client.models import Notification, Fault, Error, Computer

import logging
logger = logging.getLogger('celery')


def add_orphan_packages():
    con = get_redis_connection()
    con.hmset(
        'migasfree:chk:orphan', {
            'msg': gettext('Orphan Package/Set'),
            'target': 'server',
            'level': 'warning',
            'result': Package.orphan_count(),
            'api': reverse('package-orphan'),
        }
    )
    con.sadd('migasfree:watch:chk', 'orphan')


def add_unchecked_notifications():
    con = get_redis_connection()
    con.hmset(
        'migasfree:chk:notifications', {
            'msg': gettext('Unchecked Notifications'),
            'target': 'server',
            'level': 'warning',
            'result': Notification.objects.unchecked().count(),
            'api': '{}?checked=False'.format('notification-list')
        }
    )
    con.sadd('migasfree:watch:chk', 'notifications')


def add_unchecked_faults():
    con = get_redis_connection()
    con.hmset(
        'migasfree:chk:faults', {
            'msg': gettext('Unchecked Faults'),
            'target': 'computer',
            'level': 'critical',
            'result': Fault.unchecked_count(),
            'api': '{}?checked=False'.format('fault-list')
        }
    )
    con.sadd('migasfree:watch:chk', 'faults')


def add_unchecked_errors():
    con = get_redis_connection()
    con.hmset(
        'migasfree:chk:errors', {
            'msg': gettext('Unchecked Errors'),
            'target': 'computer',
            'level': 'critical',
            'result': Error.unchecked_count(),
            'api': '{}?checked=False'.format('error-list')
        }
    )
    con.sadd('migasfree:watch:chk', 'errors')


def add_generating_repos():
    con = get_redis_connection()
    result = con.scard('migasfree:watch:repos')
    con.hmset(
        'migasfree:chk:repos', {
            'msg': gettext('Generating Repositories'),
            'target': 'server',
            'level': 'info',
            'result': result,
            'api': reverse('internalsource-generating')
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
        date = con.hget('migasfree:msg:{}'.format(computer_id), 'date')
        if date and datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f') > delayed_time:
            result += 1

    con.hmset(
        'migasfree:chk:syncs', {
            'msg': gettext('Synchronizing Computers Now'),
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
        date = con.hget('migasfree:msg:{}'.format(computer_id), 'date')
        if date and datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f') <= delayed_time:
            result += 1

    con.hmset(
        'migasfree:chk:delayed', {
            'msg': gettext('Delayed Computers'),
            'target': 'computer',
            'level': 'critical',
            'result': result,
            'api': reverse('computer-delayed')
        }
    )
    con.sadd('migasfree:watch:chk', 'delayed')


def add_active_schedule_deployments():
    """
    With schedule, but not finished -> to relationship with errors
    """
    con = get_redis_connection()

    result = 0
    for item in Deployment.objects.filter(schedule__isnull=False, enabled=True):
        if int(item.schedule_timeline()['percent']) < 100:
            result += 1

    con.hmset(
        'migasfree:chk:active_deploys', {
            'msg': gettext('Active schedule deployments'),
            'target': 'server',
            'level': 'info',
            'result': result,
            'api': '{}?enabled__exact=1&schedule__isnull=False'.format(
                reverse('admin:core_deployment_changelist')
            ),
        }
    )
    con.sadd('migasfree:watch:chk', 'active_deploys')


def add_finished_schedule_deployments():
    """
    To convert in permanents or delete
    """
    con = get_redis_connection()

    result = 0
    for item in Deployment.objects.filter(schedule__isnull=False, enabled=True):
        if int(item.schedule_timeline()['percent']) == 100:
            result += 1

    con.hmset(
        'migasfree:chk:finished_deploys', {
            'msg': gettext('Finished schedule deployments'),
            'target': 'server',
            'level': 'warning',
            'result': result,
            'api': '{}?enabled__exact=1&schedule__isnull=False'.format(
                reverse('admin:core_deployment_changelist')
            ),
        }
    )
    con.sadd('migasfree:watch:chk', 'finished_deploys')


@shared_task(queue='default')
def alerts():
    con = get_redis_connection()

    # info
    add_generating_repos()
    add_synchronizing_computers()
    add_active_schedule_deployments()

    # warning
    add_orphan_packages()
    add_unchecked_notifications()
    add_delayed_computers()
    add_finished_schedule_deployments()

    # error
    add_unchecked_faults()
    add_unchecked_errors()

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
    key = 'migasfree:deployments:{}:computers'.format(deployment_id)
    con.delete(key)
    if computers:
        [con.sadd(key, computer_id) for computer_id in list(computers)]


@shared_task(queue='default')
def computers_deployments():
    for deploy in Deployment.objects.all():
        assigned_computers_to_deployment(deploy.id)
