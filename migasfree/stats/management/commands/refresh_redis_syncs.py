# -*- coding: utf-8 -*-

# Copyright (c) 2021-2025 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2021-2025 Alberto Gacías <alberto@migasfree.org>
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
from django_redis import get_redis_connection

from ....client.models import Synchronization


class Command(BaseCommand):
    help = 'Refresh redis syncs stats'

    INITIAL_YEAR = 2010
    CURRENT_YEAR = datetime.today().year

    def add_arguments(self, parser):
        parser.add_argument('-s', '--since', type=int, action='store', default=self.INITIAL_YEAR, help='Format: YYYY')
        parser.add_argument('-u', '--until', type=int, action='store', default=self.CURRENT_YEAR, help='Format: YYYY')
        parser.add_argument('-r', '--remove', action='store_true', help='Remove Redis stats')

    def _batch_delete_keys(self, con, year):
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

        self.stdout.write(self.style.NOTICE(f'Since year {since}'))
        self.stdout.write(self.style.NOTICE(f'Until year {until}'))
        if remove:
            self.stdout.write(self.style.NOTICE('Remove only'))

        con = get_redis_connection()

        # first, reset redis stats
        start_reset = time.perf_counter()
        for year in range(since, until + 1):
            self._batch_delete_keys(con, year)

        elapsed_reset = time.perf_counter() - start_reset
        self.stdout.write(self.style.NOTICE(f'Reset Redis stats: {elapsed_reset:.2f} s'))

        if not remove:
            # then, update db syncs
            start_update = time.perf_counter()
            for sync in Synchronization.objects.filter(
                created_at__year__gte=since, created_at__year__lte=until
            ).iterator():
                sync.add_to_redis()

            elapsed_update = time.perf_counter() - start_update
            self.stdout.write(self.style.NOTICE(f'Update DB syncs: {elapsed_update:.2f} s'))

        self.stdout.write(self.style.SUCCESS('Redis stats refreshed!'))
