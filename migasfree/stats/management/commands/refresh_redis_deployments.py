# Copyright (c) 2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2026 Alberto Gacías <alberto@migasfree.org>
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

import time

from django.core.management.base import BaseCommand
from django_redis import get_redis_connection

from ...client.models import Computer, Synchronization
from ...core.models import Deployment
from ..tasks import assigned_computers_to_deployment


class Command(BaseCommand):
    help = 'Refresh redis deployments stats (assigned, and optionally ok/error status)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Refreshing Redis deployment stats...'))
        con = get_redis_connection()

        # 1. Recalculate Assigned Computers
        self.stdout.write('Step 1/2: Recalculating assigned computers for all deployments...')
        start_assigned = time.perf_counter()
        deployments = Deployment.objects.filter(enabled=True)
        total_deploys = deployments.count()

        # Clear assigned keys first to be sure
        for key in con.scan_iter(match='migasfree:deployments:*:computers'):
            con.delete(key)

        for i, deploy in enumerate(deployments, 1):
            assigned_computers_to_deployment(deploy.id)
            if i % 10 == 0 or i == total_deploys:
                self.stdout.write(f'  Processed {i}/{total_deploys} deployments...')

        self.stdout.write(
            self.style.NOTICE(f'Assigned computers recalculated in {time.perf_counter() - start_assigned:.2f} s')
        )

        # 2. Recalculate OK/Error Status from Latest Synchronizations
        self.stdout.write('Step 2/2: Recalculating OK/Error status from latest synchronizations...')
        start_status = time.perf_counter()

        # Clear old status keys
        for key in con.scan_iter(match='migasfree:deployments:*:ok'):
            con.delete(key)
        for key in con.scan_iter(match='migasfree:deployments:*:error'):
            con.delete(key)

        # Process productive computers with sync history
        computers = Computer.productive.filter(synchronization__isnull=False).distinct()
        total_computers = computers.count()

        pipeline = con.pipeline(transaction=False)
        op_count = 0

        for i, computer in enumerate(computers, 1):
            try:
                latest_sync = Synchronization.objects.filter(computer=computer).order_by('-created_at').first()

                if latest_sync:
                    # Approximation: use current available deployments
                    available_deploys = Deployment.available_deployments(
                        computer, computer.get_all_attributes()
                    ).values_list('id', flat=True)

                    for deploy_id in available_deploys:
                        status_key = (
                            f'migasfree:deployments:{deploy_id}:{"ok" if latest_sync.pms_status_ok else "error"}'
                        )
                        pipeline.sadd(status_key, computer.id)
                        op_count += 1

                if op_count >= 5000:
                    pipeline.execute()
                    op_count = 0
            except Exception:
                # Silent failure as requested
                pass

            if i % 500 == 0 or i == total_computers:
                self.stdout.write(f'  Processed {i}/{total_computers} computers...')

        pipeline.execute()
        self.stdout.write(self.style.NOTICE(f'Status recalculated in {time.perf_counter() - start_status:.2f} s'))
        self.stdout.write(self.style.SUCCESS('Redis deployment stats refreshed successfully!'))
