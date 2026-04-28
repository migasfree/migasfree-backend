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

from migasfree.client.models import Synchronization
from migasfree.core.models import Deployment
from migasfree.core.pms import get_available_pms
from migasfree.stats.tasks import assigned_computers_to_deployment


class Command(BaseCommand):
    help = 'Refresh redis deployments stats (assigned, and optionally ok/error status)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Refreshing Redis deployment stats...'))
        con = get_redis_connection()

        # 1. Recalculate Assigned Computers
        self.stdout.write('Step 1/2: Recalculating assigned computers for deployments with schedules...')
        start_assigned = time.perf_counter()
        deployments = Deployment.objects.filter(enabled=True, schedule__isnull=False)
        total_deploys = deployments.count()

        # Clear assigned keys in bulk
        self.stdout.write('  Cleaning up old assigned keys...')
        assigned_keys = list(con.scan_iter(match='migasfree:deployments:*:computers'))
        if assigned_keys:
            con.delete(*assigned_keys)

        available_pms_names = {name for name, _ in get_available_pms()}

        for i, deploy in enumerate(deployments, 1):
            if deploy.project.pms not in available_pms_names:
                continue

            assigned_computers_to_deployment(deploy.id)
            if i % 50 == 0 or i == total_deploys:
                self.stdout.write(f'  Processed {i}/{total_deploys} deployments...')

        self.stdout.write(
            self.style.NOTICE(f'Assigned computers recalculated in {time.perf_counter() - start_assigned:.2f} s')
        )

        # 2. Recalculate OK/Error Status from Latest Synchronizations
        self.stdout.write('Step 2/2: Recalculating OK/Error status from latest synchronizations...')
        start_status = time.perf_counter()

        # Clear old status keys in bulk
        self.stdout.write('  Cleaning up old status keys...')
        status_keys = list(con.scan_iter(match='migasfree:deployments:*:ok')) + list(
            con.scan_iter(match='migasfree:deployments:*:error')
        )
        if status_keys:
            con.delete(*status_keys)

        # Efficiently get the latest synchronization for each productive computer
        # using PostgreSQL's DISTINCT ON feature.
        latest_syncs = (
            Synchronization.objects.filter(computer__productive=True)
            .order_by('computer_id', '-created_at')
            .distinct('computer_id')
            .select_related('computer')
            .iterator()
        )

        pipeline = con.pipeline(transaction=False)
        op_count = 0
        processed_count = 0

        for sync in latest_syncs:
            processed_count += 1
            try:
                computer = sync.computer
                # Approximation: use current available deployments
                available_deploys = Deployment.available_deployments(
                    computer, computer.get_all_attributes()
                ).values_list('id', flat=True)

                status_suffix = 'ok' if sync.pms_status_ok else 'error'
                for deploy_id in available_deploys:
                    pipeline.sadd(f'migasfree:deployments:{deploy_id}:{status_suffix}', computer.id)
                    op_count += 1

                if op_count >= 10000:
                    pipeline.execute()
                    op_count = 0
            except Exception:
                pass

            if processed_count % 1000 == 0:
                self.stdout.write(f'  Processed {processed_count} computers...')

        pipeline.execute()
        self.stdout.write(f'  Final computer count: {processed_count}')
        self.stdout.write(self.style.NOTICE(f'Status recalculated in {time.perf_counter() - start_status:.2f} s'))
        self.stdout.write(self.style.SUCCESS('Redis deployment stats refreshed successfully!'))
