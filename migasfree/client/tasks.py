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

from datetime import datetime

from django.db import connection
from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task
from celery.exceptions import Ignore

from migasfree.core.models import Package
from .models import Computer


@shared_task(queue='default')
def update_software_inventory(computer_id, inventory):
    try:
        computer = Computer.objects.get(pk=computer_id)
    except ObjectDoesNotExist:
        raise Ignore()

    if inventory and isinstance(inventory, list):
        pkgs = []
        for fullname in inventory:
            if fullname:
                name, version, architecture = Package.normalized_name(fullname)
                if not name:
                    continue

                pkgs.append((name, version, architecture, fullname))

        if pkgs:
            update_software_inventory_raw(pkgs, computer.id, computer.project.id)


def update_software_inventory_raw(pkgs, computer_id, project_id):
    now = datetime.now()
    cursor = connection.cursor()

    # UPDATE UNINSTALL M2M
    sql = """
    SELECT P.package_id
    FROM (VALUES %(pkgs)s) tmp(name, version, architecture, fullname)
    RIGHT JOIN (
        SELECT core_package.id as package_id, core_package.name,
            core_package.version, core_package.architecture, core_package.fullname
        FROM core_package
            LEFT JOIN client_packagehistory ON core_package.id=client_packagehistory.package_id
        WHERE client_packagehistory.computer_id=%(cid)s
            AND core_package.project_id=%(project)s
    ) AS P ON tmp.name=P.name AND tmp.version=P.version AND tmp.architecture=P.architecture
    WHERE tmp.name IS NULL;
    """ % {
        'pkgs': str(pkgs)[1:-1],
        'cid': computer_id,
        'project': project_id
    }
    cursor.execute(sql)
    to_remove = [x[0] for x in cursor.fetchall()]
    if to_remove:
        sql = """
        UPDATE client_packagehistory SET uninstall_date='%(date)s'
        WHERE client_packagehistory.package_id IN (%(pkgs)s)
            AND uninstall_date IS NULL
            AND computer_id=%(cid)s;
        """ % {
            'date': str(now),
            'pkgs': str(to_remove)[1:-1],
            'cid': computer_id
        }
        cursor.execute(sql)

    # INSERT PKG
    sql = """
    SELECT tmp.name, tmp.version, tmp.architecture, tmp.fullname
    FROM (VALUES %(pkgs)s) tmp(name, version, architecture, fullname)
    LEFT JOIN (
        SELECT core_package.name, core_package.version,
            core_package.architecture, core_package.fullname
        FROM core_package
        WHERE core_package.project_id=%(project)s
    ) AS P ON tmp.name=P.name AND tmp.version=P.version
        AND tmp.architecture=P.architecture AND tmp.fullname=P.fullname
    WHERE P.name IS NULL;
    """ % {
        'pkgs': str(pkgs)[1:-1],
        'project': project_id
    }
    cursor.execute(sql)
    to_add = [
        (
            x[0].encode('ascii', 'ignore'),
            x[1].encode('ascii', 'ignore'),
            x[2].encode('ascii', 'ignore'),
            x[3].encode('ascii', 'ignore'),
            project_id
        ) for x in cursor.fetchall()
    ]
    if to_add:
        sql = """
        INSERT INTO core_package(name, version, architecture, fullname, project_id)
        VALUES %s;
        """ % str(to_add)[1:-1]
        cursor.execute(sql)

    # INSERT M2M
    sql = """
    SELECT P.id
    FROM (VALUES %(pkgs)s) tmp(name, version)
    RIGHT JOIN (
        SELECT core_package.id AS id, core_package.name, core_package.version
        FROM core_package
        LEFT JOIN (
            SELECT package_id, computer_id
            FROM client_packagehistory
            WHERE computer_id=%(cid)s AND uninstall_date IS NULL
        ) AS C ON core_package.id=C.package_id
        WHERE core_package.project_id=%(project)s AND C.computer_id IS NULL
    ) AS P ON tmp.name=P.name AND tmp.version=P.version
    WHERE tmp.name IS NOT NULL;
    """ % {
        'pkgs': str(pkgs)[1:-1],
        'cid': computer_id,
        'project': project_id
    }
    cursor.execute(sql)
    to_m2m_history = [(computer_id, x[0], str(now)) for x in cursor.fetchall()]
    if to_m2m_history:
        sql = """
        INSERT INTO client_packagehistory(computer_id, package_id, install_date)
        VALUES %s;
        """ % str(to_m2m_history)[1:-1]
        cursor.execute(sql)
