# Copyright (c) 2021-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2021-2026 Alberto Gacías <alberto@migasfree.org>
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
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db.models.functions import TruncHour
from django_redis import get_redis_connection

from ....client.models import Synchronization


class Command(BaseCommand):
    help = 'Refresh redis syncs stats (Optimized version)'

    INITIAL_YEAR = 2010
    CURRENT_YEAR = datetime.today().year

    def add_arguments(self, parser):
        parser.add_argument('-s', '--since', type=int, action='store', default=self.INITIAL_YEAR, help='Format: YYYY')
        parser.add_argument('-u', '--until', type=int, action='store', default=self.CURRENT_YEAR, help='Format: YYYY')
        parser.add_argument('-r', '--remove', action='store_true', help='Remove Redis stats')

    def _batch_delete_keys(self, con, year):
        self.stdout.write(f'Deleting old keys for year {year}...')
        intervals = ['years', 'months', 'days', 'hours']
        all_keys = []
        for interval in intervals:
            patterns = [
                f'migasfree:stats:{interval}:{year}*',
                f'migasfree:watch:stats:{interval}:{year}*',
                f'migasfree:stats:*:{interval}:{year}*',
                f'migasfree:watch:stats:*:{interval}:{year}*',
            ]
            for pattern in patterns:
                for key in con.scan_iter(match=pattern):
                    all_keys.append(key)
        if all_keys:
            con.delete(*all_keys)

    def handle(self, *args, **options):
        since = options['since']
        until = options['until']
        remove = options['remove']

        if since > self.CURRENT_YEAR:
            since = self.INITIAL_YEAR
        if until < since:
            until = self.CURRENT_YEAR

        self.stdout.write(self.style.NOTICE(f'Refreshing Redis stats from {since} to {until}...'))
        con = get_redis_connection()

        # 1. Reset Redis stats
        start_reset = time.perf_counter()
        for year in range(since, until + 1):
            self._batch_delete_keys(con, year)
        self.stdout.write(self.style.NOTICE(f'Reset finished in {time.perf_counter() - start_reset:.2f} s'))

        if not remove:
            # 2. Bulk SADD with Pipeline
            self.stdout.write(self.style.NOTICE('Querying unique computer/hour slots (SQL Distinct)...'))
            start_update = time.perf_counter()

            # Group by hour in SQL to drastically reduce processing rows
            syncs = (
                Synchronization.objects.filter(created_at__year__gte=since, created_at__year__lte=until)
                .annotate(hour=TruncHour('created_at'))
                .values('computer_id', 'project_id', 'hour')
                .distinct()
                .iterator()
            )

            pipeline = con.pipeline(transaction=False)
            op_count = 0
            total_slots = 0

            self.stdout.write('Populating Redis sets...')
            for sync in syncs:
                h = sync['hour']
                c_id = sync['computer_id']
                p_id = sync['project_id']

                y_s = f'{h.year:04}'
                m_s = f'{y_s}{h.month:02}'
                d_s = f'{m_s}{h.day:02}'
                h_s = f'{d_s}{h.hour:02}'

                # SADD all granularity levels (Global and per Project)
                # Redis SADD returns 1 if element is new, but we use SCARD later for safety
                pipeline.sadd(f'migasfree:watch:stats:years:{y_s}', c_id)
                pipeline.sadd(f'migasfree:watch:stats:{p_id}:years:{y_s}', c_id)
                pipeline.sadd(f'migasfree:watch:stats:months:{m_s}', c_id)
                pipeline.sadd(f'migasfree:watch:stats:{p_id}:months:{m_s}', c_id)
                pipeline.sadd(f'migasfree:watch:stats:days:{d_s}', c_id)
                pipeline.sadd(f'migasfree:watch:stats:{p_id}:days:{d_s}', c_id)
                pipeline.sadd(f'migasfree:watch:stats:hours:{h_s}', c_id)
                pipeline.sadd(f'migasfree:watch:stats:{p_id}:hours:{h_s}', c_id)

                op_count += 8
                total_slots += 1

                if op_count >= 10000:
                    pipeline.execute()
                    op_count = 0
                    if total_slots % 50000 == 0:
                        self.stdout.write(f'  Processed {total_slots} unique slots...')

            pipeline.execute()
            self.stdout.write(self.style.NOTICE(f'Sets filled in {time.perf_counter() - start_update:.2f} s'))

            # 3. Final Step: Sync counters with SCARD
            self.stdout.write(self.style.NOTICE('Synchronizing counters from sets (SCARD)...'))
            start_scard = time.perf_counter()

            all_watch_keys = []
            for year in range(since, until + 1):
                for key in con.scan_iter(match=f'migasfree:watch:stats:*{year}*'):
                    all_watch_keys.append(key.decode() if isinstance(key, bytes) else key)

            # Batch SCARD and SET
            pipeline = con.pipeline(transaction=False)
            for i, key in enumerate(all_watch_keys):
                pipeline.scard(key)
                if (i + 1) % 5000 == 0 or (i + 1) == len(all_watch_keys):
                    results = pipeline.execute()
                    set_pipe = con.pipeline(transaction=False)
                    for j, val in enumerate(results):
                        original_key = all_watch_keys[i - len(results) + 1 + j]
                        stats_key = original_key.replace(':watch:stats:', ':stats:')
                        set_pipe.set(stats_key, val)
                    set_pipe.execute()

            self.stdout.write(self.style.NOTICE(f'Counters synced in {time.perf_counter() - start_scard:.2f} s'))
            self.stdout.write(
                self.style.SUCCESS(f'Redis stats refreshed! Total time: {time.perf_counter() - start_reset:.2f} s')
            )
        else:
            self.stdout.write(self.style.SUCCESS('Redis stats removed!'))
