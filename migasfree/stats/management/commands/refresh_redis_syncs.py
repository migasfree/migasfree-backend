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

from django.core.management.base import BaseCommand, CommandError
from django_redis import get_redis_connection

from ....client.models import Synchronization


class Command(BaseCommand):
    help = 'Refresh redis syncs stats'

    def handle(self, *args, **options):
        # first, reset stats
        con = get_redis_connection()
        for x in con.keys('migasfree:stats*'):
            con.delete(x)
        for x in con.keys('migasfree:watch:stats*'):
            con.delete(x)

        self.stdout.write(self.style.SUCCESS('Redis stats reset!'))

        # then, update db syncs
        for sync in Synchronization.objects.all():
            sync.add_to_redis()

        self.stdout.write(self.style.SUCCESS('Redis stats refreshed!'))
