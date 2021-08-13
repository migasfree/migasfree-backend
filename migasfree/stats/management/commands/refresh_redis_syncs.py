# -*- coding: utf-8 -*-

# Copyright (c) 2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2021 Alberto Gacías <alberto@migasfree.org>
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

from datetime import datetime

from django.core.management.base import BaseCommand
from django_redis import get_redis_connection

from ....client.models import Synchronization


class Command(BaseCommand):
    help = 'Refresh redis syncs stats'

    INITIAL_YEAR = 2010
    CURRENT_YEAR = datetime.today().year

    def add_arguments(self, parser):
        parser.add_argument(
            '-s', '--since',
            type=int, action='store', default=self.INITIAL_YEAR,
            help='Format: YYYY'
        )
        parser.add_argument(
            '-u', '--until',
            type=int, action='store', default=self.CURRENT_YEAR,
            help='Format: YYYY'
        )
        parser.add_argument(
            '-r', '--remove',
            action='store_true',
            help='Remove Redis stats'
        )

    def handle(self, *args, **options):
        since = options['since']
        until = options['until']
        remove = options['remove']
        if since > self.CURRENT_YEAR:
            since = self.INITIAL_YEAR
        if until < since:
            until = self.CURRENT_YEAR

        self.stdout.write(self.style.NOTICE('Since year {}'.format(since)))
        self.stdout.write(self.style.NOTICE('Until year {}'.format(until)))
        if remove:
            self.stdout.write(self.style.NOTICE('Remove only'))

        con = get_redis_connection()

        # first, reset redis stats
        for year in range(since, until + 1):
            for interval in ['years', 'months', 'days', 'hours']:
                for x in con.keys('migasfree:stats:{}:{}*'.format(interval, year)):
                    con.delete(x)

                for x in con.keys('migasfree:watch:stats:{}:{}*'.format(interval, year)):
                    con.delete(x)

                for x in con.keys('migasfree:stats:*:{}:{}*'.format(interval, year)):
                    con.delete(x)

                for x in con.keys('migasfree:watch:stats:*:{}:{}*'.format(interval, year)):
                    con.delete(x)

        if not remove:
            # then, update db syncs
            for sync in Synchronization.objects.filter(
                    created_at__year__gte=since,
                    created_at__year__lte=until
            ).iterator():
                sync.add_to_redis()

        self.stdout.write(self.style.SUCCESS('Redis stats refreshed!'))
