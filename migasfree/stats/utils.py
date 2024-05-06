# -*- coding: utf-8 -*-

# Copyright (c) 2024 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2024 Alberto Gacías <alberto@migasfree.org>
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

from datetime import datetime, timedelta
from operator import gt

from django.conf import settings
from django.utils import timezone
from django_redis import get_redis_connection


def filter_computers_by_date(comparison_operator=gt):
    con = get_redis_connection()

    result = []
    delayed_time = timezone.localtime(timezone.now()) - timedelta(seconds=settings.MIGASFREE_SECONDS_MESSAGE_ALERT)

    computers = con.smembers('migasfree:watch:msg')
    for computer_id in computers:
        date = con.hget(f'migasfree:msg:{int(computer_id)}', 'date')
        aware_date = timezone.make_aware(
            datetime.strptime(date.decode(), '%Y-%m-%dT%H:%M:%S.%f'),
            timezone.get_default_timezone()
        ) if date else None
        if aware_date and comparison_operator(aware_date, delayed_time):
            result.append(int(computer_id))

    return result, delayed_time
