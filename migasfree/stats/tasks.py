# -*- coding: utf-8 -*-

# Copyright (c) 2015-2024 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2024 Alberto Gacías <alberto@migasfree.org>
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

import json

from datetime import datetime, timedelta

from asgiref.sync import async_to_sync
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext
from celery import shared_task
from channels.layers import get_channel_layer
from django_redis import get_redis_connection

from ..core.models import Package, PackageSet, Deployment
from ..client.models import Notification, Fault, Error, Computer
from ..utils import decode_set, decode_dict


import logging
logger = logging.getLogger('celery')


def add_orphan_packages():
    con = get_redis_connection()
    con.hmset(
        'migasfree:chk:orphan_packages', {
            'msg': gettext('Orphan Packages'),
            'target': 'server',
            'level': 'warning',
            'result': Package.orphan_count(),
            'api': json.dumps({
                'model': 'packages',
                'query': {
                    'deployment': True,  # isnull = True
                    'store': False,  # isnull = False
                    'packageset': True  # isnull = True
                }
            })
        }
    )
    con.sadd('migasfree:watch:chk', 'orphan_packages')


def add_orphan_package_sets():
    con = get_redis_connection()
    con.hmset(
        'migasfree:chk:orphan_package_sets', {
            'msg': gettext('Orphan Package Sets'),
            'target': 'server',
            'level': 'warning',
            'result': PackageSet.orphan_count(),
            'api': json.dumps({
                'model': 'package_sets',
                'query': {
                    'deployment': True,  # isnull = True
                    'packages': False  # isnull = False
                }
            })
        }
    )
    con.sadd('migasfree:watch:chk', 'orphan_package_sets')


def add_unchecked_notifications():
    con = get_redis_connection()
    con.hmset(
        'migasfree:chk:notifications', {
            'msg': gettext('Unchecked Notifications'),
            'target': 'server',
            'level': 'warning',
            'result': Notification.objects.unchecked().count(),
            'api': json.dumps({
                'model': 'notifications',
                'query': {
                    'checked': False
                }
            })
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
            'api': json.dumps({
                'model': 'faults',
                'query': {
                    'checked': False,
                    'user': 'me',
                }
            })
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
            'api': json.dumps({
                'model': 'errors',
                'query': {
                    'checked': False
                }
            })
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
            'api': json.dumps({
                'model': 'deployments',
                'query': {
                    'id_in': ','.join(decode_set(con.smembers('migasfree:watch:repos')))
                }
            })
        }
    )
    con.sadd('migasfree:watch:chk', 'repos')


def add_synchronizing_computers():
    con = get_redis_connection()

    result = 0
    delayed_time = timezone.now() - timedelta(
        seconds=settings.MIGASFREE_SECONDS_MESSAGE_ALERT
    )

    computers = con.smembers('migasfree:watch:msg')
    for computer_id in computers:
        computer_id = int(computer_id)
        date = con.hget(f'migasfree:msg:{computer_id}', 'date')
        aware_date = timezone.make_aware(
            datetime.strptime(date.decode(), '%Y-%m-%dT%H:%M:%S.%f'),
            timezone.get_default_timezone()
        ) if date else None
        if aware_date and aware_date > delayed_time:
            result += 1

    con.hmset(
        'migasfree:chk:syncs', {
            'msg': gettext('Synchronizing Computers Now'),
            'target': 'computer',
            'level': 'info',
            'result': result,
            'api': json.dumps({
                'model': 'messages',
                'query': {
                    'created_at__gte': datetime.strftime(delayed_time, '%Y-%m-%dT%H:%M:%S')
                }
            })
        }
    )
    con.sadd('migasfree:watch:chk', 'syncs')


def add_delayed_computers():
    con = get_redis_connection()

    result = 0
    delayed_time = timezone.now() - timedelta(
        seconds=settings.MIGASFREE_SECONDS_MESSAGE_ALERT
    )

    computers = con.smembers('migasfree:watch:msg')
    for computer_id in computers:
        computer_id = int(computer_id)
        date = con.hget(f'migasfree:msg:{computer_id}', 'date')
        aware_date = timezone.make_aware(
            datetime.strptime(date.decode(), '%Y-%m-%dT%H:%M:%S.%f'),
            timezone.get_default_timezone()
        ) if date else None
        if aware_date and aware_date <= delayed_time:
            result += 1

    con.hmset(
        'migasfree:chk:delayed', {
            'msg': gettext('Delayed Computers'),
            'target': 'computer',
            'level': 'warning',
            'result': result,
            'api': json.dumps({
                'model': 'messages',
                'query': {
                    'created_at__lt': datetime.strftime(delayed_time, '%Y-%m-%dT%H:%M:%S')
                }
            })
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
            'api': json.dumps({
                'model': 'deployments',
                'query': {
                    'enabled': True,
                    'schedule': False,  # isnull = False
                    'percent__lt': 100
                }
            })
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
            'api': json.dumps({
                'model': 'deployments',
                'query': {
                    'enabled': True,
                    'schedule': False,  # isnull = False
                    'percent__gte': 100
                }
            })
        }
    )
    con.sadd('migasfree:watch:chk', 'finished_deploys')


def get_alerts():
    con = get_redis_connection()

    response = [
        decode_dict(con.hgetall('migasfree:chk:repos')),
        decode_dict(con.hgetall('migasfree:chk:syncs')),
        decode_dict(con.hgetall('migasfree:chk:active_deploys')),
        decode_dict(con.hgetall('migasfree:chk:orphan_packages')),
        decode_dict(con.hgetall('migasfree:chk:orphan_package_sets')),
        decode_dict(con.hgetall('migasfree:chk:notifications')),
        decode_dict(con.hgetall('migasfree:chk:delayed')),
        decode_dict(con.hgetall('migasfree:chk:finished_deploys')),
        decode_dict(con.hgetall('migasfree:chk:faults')),
        decode_dict(con.hgetall('migasfree:chk:errors')),
    ]

    for item in response:
        item['api'] = json.loads(item.get('api', '{}'))
        item['msg'] = gettext(item.get('msg', ''))

    return [item for item in response if not (int(item['result']) == 0)]


@shared_task(queue='default')
def alerts():
    con = get_redis_connection()

    # info
    add_generating_repos()
    add_synchronizing_computers()
    add_active_schedule_deployments()

    # warning
    add_orphan_packages()
    add_orphan_package_sets()
    add_unchecked_notifications()
    add_delayed_computers()
    add_finished_schedule_deployments()

    # error
    add_unchecked_faults()
    add_unchecked_errors()

    logger.debug(con.smembers('migasfree:watch:chk'))

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)('stats', {
        'type': 'send_alerts',
        'text': get_alerts()
    })


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
    key = f'migasfree:deployments:{deployment_id}:computers'
    con.delete(key)
    if computers:
        for computer_id in list(computers):
            con.sadd(key, computer_id)


@shared_task(queue='default')
def computers_deployments():
    for deploy in Deployment.objects.all():
        assigned_computers_to_deployment(deploy.id)
