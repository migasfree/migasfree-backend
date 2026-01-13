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

"""
Base classes and mixins for serializers.
"""


class AttributeRepresentationMixin:
    """
    Mixin to reduce code duplication in serializers that handle
    included_attributes and excluded_attributes fields.

    Override attribute_fields to customize which fields are serialized.
    """

    attribute_fields = ['included_attributes', 'excluded_attributes']

    def to_representation(self, obj):
        # Import here to avoid circular dependency
        from .property import AttributeInfoSerializer

        representation = super().to_representation(obj)
        for field in self.attribute_fields:
            if hasattr(obj, field):
                representation[field] = [AttributeInfoSerializer(item).data for item in getattr(obj, field).all()]
        return representation
