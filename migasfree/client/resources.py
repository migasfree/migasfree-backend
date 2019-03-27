# -*- coding: utf-8 -*-

# Copyright (c) 2019 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2019 Alberto Gacías <alberto@migasfree.org>
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

from import_export import resources

from .models import Computer


class ComputerResource(resources.ModelResource):
    def dehydrate_project(self, computer):
        return computer.project.name

    def dehydrate_sync_user(self, computer):
        return computer.sync_user

    class Meta:
        model = Computer
        exclude = (
            'software_history',
            'software_inventory',
            'sync_attributes',
            'default_logical_device',
        )
