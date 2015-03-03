# -*- coding: utf-8 *-*

# Copyright (c) 2015 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015 Alberto Gacías <alberto@migasfree.org>
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

from django.conf import settings
from django.contrib import auth
from rest_framework import permissions


class IsPackager(permissions.BasePermission):
    def has_permission(self, request, view):
        user = auth.authenticate(
            username=request.data.get('username'),
            password=request.data.get('password')
        )
        if not user:
            return False

        return user.is_superuser or user.has_perm('core.change_package')


class IsClient(permissions.BasePermission):
    def has_permission(self, request, view):
        if settings.MIGASFREE_AUTOREGISTER:
            return True

        user = auth.authenticate(
            username=request.data.get('username'),
            password=request.data.get('password')
        )
        if not user:
            return False

        return (user.has_perm('core.change_platform')
            and user.has_perm('core.change_project')
            and user.has_perm('client.change_computer')
        )
