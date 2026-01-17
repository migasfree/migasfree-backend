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

"""Packager key retrieval functions."""

from django.contrib import auth

from .. import errmfs
from ..secure import get_keys_to_packager
from .helpers import return_message


def get_key_packager(request, name, uuid, computer, data):
    cmd = 'get_key_packager'
    user = auth.authenticate(username=data['username'], password=data['password'])
    if not user or not user.has_perm('core.add_package') or not user.has_perm('core.change_package'):
        return return_message(cmd, errmfs.error(errmfs.CAN_NOT_REGISTER_COMPUTER))

    return return_message(cmd, get_keys_to_packager())
