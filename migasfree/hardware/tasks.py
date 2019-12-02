# -*- coding: utf-8 -*-

# Copyright (c) 2015-2018 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2018 Alberto Gacías <alberto@migasfree.org>
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

from migasfree.client.models import Computer

from .models import Node, Capability, LogicalName, Configuration

import logging
logger = logging.getLogger('celery')

MAXINT = 9223372036854775807  # sys.maxint = (2**63) - 1


@shared_task(queue='default')
def save_computer_hardware(computer_id, node, parent=None, level=1):
    computer = Computer.objects.get(id=computer_id)
    size = node.get('size')
    n = Node.objects.create({
        'parent': parent,
        'computer': computer,
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
        'size': size if (MAXINT >= size >= -MAXINT - 1) else 0,
        'capacity': node.get('capacity'),
        'clock': node.get('clock'),
        'width': node.get('width'),
        'dev': node.get('dev')
    })

    level += 1

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
            if isinstance(node[e], str):
                LogicalName.objects.create(node=n, name=node[e])
            else:
                for x in node[e]:
                    LogicalName.objects.create(node=n, name=x)

    computer.update_hardware_resume()
