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

from celery import shared_task
from celery.exceptions import Ignore
from django_redis import get_redis_connection
from rest_framework.reverse import reverse

from migasfree.core.models import Package
from migasfree.client.models import Notification, Fault, Error

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
