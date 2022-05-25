# -*- coding: utf-8 -*-

# Copyright (c) 2018-2022 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2018-2022 Alberto Gacías <alberto@migasfree.org>
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

from .models import (
    Attribute, AttributeSet, ClientAttribute, ServerAttribute,
    Property, ClientProperty, ServerProperty,
    Project, Platform, UserProfile,
)


class AttributeResource(resources.ModelResource):
    computers = fields.Field()
    prefix = fields.Field()

    class Meta:
        model = Attribute
        export_order = (
            'id', 'property_att', 'prefix', 'value',
            'description', 'computers',
            'latitude', 'longitude'
        )

    def dehydrate_computers(self, attribute):
        return attribute.total_computers()

    def dehydrate_prefix(self, attribute):
        return attribute.property_att.prefix


class AttributeSetResource(resources.ModelResource):
    enabled = fields.Field(
        attribute='enabled',
        widget=widgets.BooleanWidget()
    )
    included_attributes = fields.Field(
        attribute='included_attributes',
        widget=widgets.ManyToManyWidget(Attribute)
    )
    excluded_attributes = fields.Field(
        attribute='excluded_attributes',
        widget=widgets.ManyToManyWidget(Attribute)
    )

    class Meta:
        model = AttributeSet
        export_order = (
            'id', 'name', 'enabled', 'description',
            'included_attributes', 'excluded_attributes',
            'longitude', 'latitude'
        )


class ClientAttributeResource(AttributeResource):
    class Meta:
        model = ClientAttribute


class ServerAttributeResource(AttributeResource):
    class Meta:
        model = ServerAttribute


class PropertyResource(resources.ModelResource):
    class Meta:
        model = Property
        fields = (
            'id', 'prefix', 'name',
            'enabled', 'kind', 'sort', 'auto_add',
            'language', 'code'
        )


class ClientPropertyResource(PropertyResource):
    class Meta:
        model = ClientProperty


class ServerPropertyResource(resources.ModelResource):
    class Meta:
        model = ServerProperty
        fields = ('id', 'prefix', 'name', 'enabled', 'kind', 'sort')


class ProjectResource(resources.ModelResource):
    auto_register_computers = fields.Field(
        attribute='auto_register_computers',
        widget=widgets.BooleanWidget()
    )

    class Meta:
        model = Project
        fields = ('id', 'name', 'pms', 'auto_register_computers', 'platform__name')
        export_order = ('id', 'name', 'pms', 'auto_register_computers', 'platform__name')


class PlatformResource(resources.ModelResource):
    class Meta:
        model = Platform


class UserProfileResource(resources.ModelResource):
    class Meta:
        model = UserProfile
        exclude = ('user_ptr', 'password')
