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

from migasfree.core.models import Deployment
from migasfree.core.pms import get_available_pms
from migasfree.stats.tasks import assigned_computers_to_deployment


class Command(BaseCommand):
    help = 'Refresh redis deployments stats (assigned)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Refreshing Redis deployment stats...'))
        con = get_redis_connection()

        # 1. Recalculate Assigned Computers
        self.stdout.write('Recalculating assigned computers for enabled deployments with schedules...')
        start_assigned = time.perf_counter()
        deployments = Deployment.objects.filter(enabled=True, schedule__isnull=False)
        total_deploys = deployments.count()

        # Clear assigned keys in bulk
        self.stdout.write('  Cleaning up old assigned keys...')
        assigned_keys = list(con.scan_iter(match='migasfree:deployments:*:computers'))
        if assigned_keys:
            con.delete(*assigned_keys)

        # Clear old status keys in bulk (they will remain empty as we can't reliably estimate from v4)
        self.stdout.write('  Cleaning up old status keys...')
        status_keys = list(con.scan_iter(match='migasfree:deployments:*:ok')) + list(
            con.scan_iter(match='migasfree:deployments:*:error')
        )
        if status_keys:
            con.delete(*status_keys)

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
        self.stdout.write(self.style.SUCCESS('Redis deployment stats refreshed successfully!'))
