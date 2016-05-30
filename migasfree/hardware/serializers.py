# -*- coding: utf-8 -*-

# Copyright (c) 2015-2016 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2016 Alberto Gacías <alberto@migasfree.org>
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

from rest_framework import serializers

from . import models


class NodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Node
        fields = (
            'id', 'product', 'parent', 'name', 'level', 'width',
            'class_name', 'enabled', 'claimed', 'description',
            'vendor', 'version', 'serial', 'bus_info', 'physid',
            'slot', 'size', 'capacity', 'clock', 'dev', 'computer'
        )
