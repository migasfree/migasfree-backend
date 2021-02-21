# -*- coding: utf-8 -*-

# Copyright (c) 2018-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2018-2021 Alberto Gacías <alberto@migasfree.org>
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

from import_export import resources, fields, widgets

from .models import Attribute, ClientAttribute, ServerAttribute, Project


class AttributeResource(resources.ModelResource):
    computers = fields.Field()
    prefix = fields.Field()

    class Meta:
        model = Attribute
        export_order = ('id', 'property_att', 'prefix', 'value', 'description', 'computers')

    def dehydrate_computers(self, attribute):
        return attribute.total_computers()

    def dehydrate_prefix(self, attribute):
        return attribute.property_att.prefix


class ClientAttributeResource(AttributeResource):
    class Meta:
        model = ClientAttribute


class ServerAttributeResource(AttributeResource):
    class Meta:
        model = ServerAttribute


class ProjectResource(resources.ModelResource):
    auto_register_computers = fields.Field(
        attribute='auto_register_computers',
        widget=widgets.BooleanWidget()
    )

    class Meta:
        model = Project
        fields = ('name', 'pms', 'auto_register_computers', 'platform__name')
