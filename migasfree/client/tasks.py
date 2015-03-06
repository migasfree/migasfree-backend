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

from .models import Package, Computer


@shared_task(queue='default')
def update_software_inventory(computer_id, inventory):
    try:
        computer = Computer.objects.get(pk=computer_id)
    except:
        raise Ignore()

    if inventory and type(inventory) == list:
        pkgs = []
        new_pkgs = []
        for package in inventory:
            if package:
                # name_version_architecture.ext convention
                try:
                    name, version, architecture = package.split('_')
                except:
                    if package.count('_') > 2:
                        slices = package.split('_', 1)
                        name = slices[0]
                        version, architecture = slices[1].rsplit('_', 1)
                    else:
                        continue

                architecture = architecture.split('.')[0]
                try:
                    pkgs.append(Package.objects.get(
                        fullname=package, project__id=computer.project.id
                    ))
                except:
                    new_pkgs.append(
                        Package(
                            fullname=package,
                            name=name, version=version,
                            architecture=architecture,
                            project=computer.project
                        )
                    )

        if new_pkgs:
            bulk = Package.objects.bulk_create(new_pkgs)
            objs = Package.objects.filter(fullname__in=bulk)
            [pkgs.append(x) for x in objs]

        computer.update_software_inventory(pkgs)
