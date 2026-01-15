# Copyright (c) 2015-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2026 Alberto Gacías <alberto@migasfree.org>
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

from asgiref.sync import async_to_sync
from celery import shared_task
from celery.exceptions import Reject
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.utils import timezone
from django_redis import get_redis_connection

from ..core.models import Package
from .models import Computer
from .saturation import get_saturation_metrics


@shared_task(queue='default')
def process_sync_queue():
    """
    Process the sync queue with adaptive concurrency.
    """
    metrics = get_saturation_metrics()
    if metrics['saturated']:
        return

    try:
        con = get_redis_connection('default')
        count = 0
        limit = getattr(settings, 'MIGASFREE_SYNC_MAX_CONCURRENCY', 50)
        max_load = getattr(settings, 'MIGASFREE_SYNC_MAX_CORE_LOAD', 90)

        # Adaptive Batch Sizing
        # 1. Calculate headroom (how much capacity is left)
        # utilization_ratio = current_load / max_allowed_load
        # capacity_factor = 1.0 - utilization_ratio
        current_load = metrics['load_percentage']
        utilization_ratio = current_load / max_load if max_load > 0 else 1.0
        capacity_factor = 1.0 - utilization_ratio

        # Clamp factor between 0.0 and 1.0
        capacity_factor = max(0.0, min(1.0, capacity_factor))

        # Calculate batch size
        batch_size = int(limit * capacity_factor)

        # Ensure minimal throughput if not strictly saturated to avoid starvation,
        # but respect the math if we are very close to the limit.
        # Let's say min 1 unless capacity_factor is super low.
        batch_size = max(1, batch_size) if capacity_factor > 0.05 else 0

        # Log for debugging (print for now, should be logger)
        if batch_size > 0:
            print(f'Sync Queue: Load {current_load:.1f}%/{max_load}%. Processing {batch_size} clients.')

        channel_layer = get_channel_layer()

        while count < batch_size:
            cid = con.lpop('migasfree_sync_queue')
            if not cid:
                break

            # Convert bytes to string if needed
            if isinstance(cid, bytes):
                cid = cid.decode('utf-8')

            # Execute remote sync via WebSocket
            # We assume channel group is 'tunnel-{cid}'
            async_to_sync(channel_layer.group_send)(
                f'tunnel-{cid}', {'type': 'execute_command', 'command': 'migasfree sync'}
            )
            count += 1

    except Exception as e:
        # Log error?
        print(f'Error processing sync queue: {e}')


@shared_task(queue='default')
def update_software_inventory(computer_id, inventory):
    try:
        computer = Computer.objects.get(pk=computer_id)
    except ObjectDoesNotExist:
        raise Reject(reason='Computer does not exist')  # noqa: B904

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
    now = timezone.localtime(timezone.now())
    cursor = connection.cursor()

    # UPDATE UNINSTALL M2M
    sql = f"""
    SELECT P.package_id
    FROM (VALUES {str(pkgs)[1:-1]}) tmp(name, version, architecture, fullname)
    RIGHT JOIN (
        SELECT core_package.id as package_id, core_package.name,
            core_package.version, core_package.architecture, core_package.fullname
        FROM core_package
            LEFT JOIN client_packagehistory ON core_package.id=client_packagehistory.package_id
        WHERE client_packagehistory.computer_id={computer_id}
            AND core_package.project_id={project_id}
    ) AS P ON tmp.name=P.name AND tmp.version=P.version AND tmp.architecture=P.architecture
    WHERE tmp.name IS NULL;
    """
    cursor.execute(sql)
    to_remove = [x[0] for x in cursor.fetchall()]
    if to_remove:
        sql = f"""
        UPDATE client_packagehistory SET uninstall_date='{now!s}'
        WHERE client_packagehistory.package_id IN ({str(to_remove)[1:-1]})
            AND uninstall_date IS NULL
            AND computer_id={computer_id};
        """
        cursor.execute(sql)

    # INSERT PKG
    sql = f"""
    SELECT tmp.name, tmp.version, tmp.architecture, tmp.fullname
    FROM (VALUES {str(pkgs)[1:-1]}) tmp(name, version, architecture, fullname)
    LEFT JOIN (
        SELECT core_package.name, core_package.version,
            core_package.architecture, core_package.fullname
        FROM core_package
        WHERE core_package.project_id={project_id}
    ) AS P ON tmp.name=P.name AND tmp.version=P.version
        AND tmp.architecture=P.architecture AND tmp.fullname=P.fullname
    WHERE P.name IS NULL;
    """
    cursor.execute(sql)
    to_add = [
        (
            x[0],  # name
            x[1],  # version
            x[2],  # architecture
            x[3],  # fullname
            project_id,
        )
        for x in cursor.fetchall()
    ]
    if to_add:
        sql = f"""
        INSERT INTO core_package(name, version, architecture, fullname, project_id)
        VALUES {str(to_add)[1:-1]};
        """
        cursor.execute(sql)

    # INSERT M2M
    sql = f"""
    SELECT P.id
    FROM (VALUES {str(pkgs)[1:-1]}) tmp(name, version)
    RIGHT JOIN (
        SELECT core_package.id AS id, core_package.name, core_package.version
        FROM core_package
        LEFT JOIN (
            SELECT package_id, computer_id
            FROM client_packagehistory
            WHERE computer_id={computer_id} AND uninstall_date IS NULL
        ) AS C ON core_package.id=C.package_id
        WHERE core_package.project_id={project_id} AND C.computer_id IS NULL
    ) AS P ON tmp.name=P.name AND tmp.version=P.version
    WHERE tmp.name IS NOT NULL;
    """
    cursor.execute(sql)
    to_m2m_history = [(computer_id, x[0], str(now)) for x in cursor.fetchall()]
    if to_m2m_history:
        sql = f"""
        INSERT INTO client_packagehistory(computer_id, package_id, install_date)
        VALUES {str(to_m2m_history)[1:-1]};
        """
        cursor.execute(sql)
