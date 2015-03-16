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
    computer = Computer.objects.get(id=computer_id)

    n = Node()
    n.parent = parent
    n.computer = computer
    n.level = level
    n.name = str(node.get('id'))
    n.class_name = node.get('class')

    if "enabled" in node:
        n.enabled = node["enabled"]
    if "claimed" in node:
        n.claimed = node["claimed"]
    if "description" in node:
        n.description = node["description"]
    if "vendor" in node:
        n.vendor = node["vendor"]
    if "product" in node:
        n.product = node["product"]
    if "version" in node:
        n.version = node["version"]
    if "serial" in node:
        n.serial = node["serial"]
    if "businfo" in node:
        n.bus_info = node["businfo"]
    if "physid" in node:
        n.physid = node["physid"]
    if "slot" in node:
        n.slot = node["slot"]
    if "size" in node:
        n.size = int(node["size"])
    if "capacity" in node:
        n.capacity = node["capacity"]
    if "clock" in node:
        n.clock = node["clock"]
    if "width" in node:
        n.width = node["width"]
    if "dev" in node:
        n.dev = node["dev"]

    n.save()
    level += 3

    for e in node:
        if e == "children":
            for x in node[e]:
                save_computer_hardware(computer_id, x, n, level)
        elif e == "capabilities":
            for x in node[e]:
                c = Capability()
                c.node = n
                c.name = x
                c.description = node[e][x]
                c.save()
        elif e == "configuration":
            for x in node[e]:
                c = Configuration()
                c.node = n
                c.name = x
                c.value = node[e][x]
                c.save()
        elif e == "logicalname":
            if type(node[e]) == unicode:
                c = LogicalName()
                c.node = n
                c.name = node[e]
                c.save()
            else:
                for x in node[e]:
                    c = LogicalName()
                    c.node = n
                    c.name = x
                    c.save()
        elif e == "resource":
            print(e, node[e])  # FIXME ???
