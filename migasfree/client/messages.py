# -*- coding: utf-8 *-*

# Copyright (c) 2022-2025 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2022-2025 Alberto Gacías <alberto@migasfree.org>
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

from django.utils import timezone

from django_redis import get_redis_connection


def add_computer_message(computer, message):
    con = get_redis_connection()
    con.hset(
        f'migasfree:msg:{computer.id}', mapping={
            'date': timezone.localtime(timezone.now()).strftime('%Y-%m-%dT%H:%M:%S.%f'),
            'computer_id': computer.id,
            'computer_name': str(computer),
            'computer_status': computer.status,
            'computer_summary': computer.get_summary(),
            'project_id': computer.project.id,
            'project_name': computer.project.name,
            'user_id': computer.sync_user.id if computer.sync_user else 0,
            'user_name': computer.sync_user.name if computer.sync_user else '',
            'msg': message
        }
    )
    con.sadd('migasfree:watch:msg', computer.id)


def remove_computer_messages(computer_id):
    con = get_redis_connection()
    keys = con.hkeys(f'migasfree:msg:{computer_id}')
    if keys:
        con.hdel(f'migasfree:msg:{computer_id}', *keys)

    con.srem('migasfree:watch:msg', computer_id)
