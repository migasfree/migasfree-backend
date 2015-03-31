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

import logging
logger = logging.getLogger('celery')

from migasfree.client.models import Computer

from .models import Node, Capability, LogicalName, Configuration


@shared_task(queue='default')
def save_computer_hardware(computer_id, node, parent=None, level=1):
    n = Node.objects.create({
        'parent': parent,
        'computer': Computer.objects.get(id=computer_id),
        'level': level,
        'name': str(node.get('id')),
        'class_name': node.get('class'),
        'enabled': node.get('enabled', False),
        'claimed': node.get('claimed', False),
        'description': node.get('description'),
        'vendor': node.get('vendor'),
        'product': node.get('product'),
        'version': node.get('version'),
        'serial': node.get('serial'),
        'bus_info': node.get('businfo'),
        'physid': node.get('physid'),
        'slot': node.get('slot'),
        'size': node.get('size'),
        'capacity': node.get('capacity'),
        'clock': node.get('clock'),
        'width': node.get('width'),
        'dev': node.get('dev')
    })

    level += 3  # FIXME ???

    for e in node:
        if e == 'children':
            for x in node[e]:
                save_computer_hardware(computer_id, x, n, level)
        elif e == 'capabilities':
            for x in node[e]:
                Capability.objects.create(
                    node=n, name=x, description=node[e][x]
                )
        elif e == 'configuration':
            for x in node[e]:
                Configuration.objects.create(node=n, name=x, value=node[e][x])
        elif e == 'logicalname':
            if type(node[e]) == unicode:
                LogicalName.objects.create(node=n, name=node[e])
            else:
                for x in node[e]:
                    LogicalName.objects.create(node=n, name=x)
