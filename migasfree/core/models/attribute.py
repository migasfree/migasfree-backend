# -*- coding: utf-8 -*-

# Copyright (c) 2015-2023 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2023 Alberto Gacías <alberto@migasfree.org>
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

import json

from django.db import models
from django.db.models import Q
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .migas_link import MigasLink
from .property import Property


class DomainAttributeManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('property_att')

    def scope(self, user):
        qs = self.get_queryset()
        if not user.is_view_all():
            qs = qs.filter(
                Q(id__in=user.get_attributes()) |
                Q(id__in=user.get_domain_tags())
            ).distinct()

        return qs


class AttributeManager(DomainAttributeManager):
    def create(
        self, property_att, value,
        description=None, longitude=None, latitude=None
    ):
        """
        if value = "text~other", description = "other"
        """
        from ...client.models import Notification

        if value.count('~') == 1:
            value, description = value.split('~')

        value = value.strip()  # clean field
        original_value = value

        if len(value) > Attribute.VALUE_LEN:
            value = value[:Attribute.VALUE_LEN]

        queryset = Attribute.objects.filter(
            property_att=property_att, value=value
        )
        if queryset.exists():
            return queryset[0]

        if property_att.auto_add is False:
            raise ValidationError(
                _('The attribute cannot be created because'
                  ' property prevents it')
            )

        obj = Attribute()
        obj.property_att = property_att
        obj.value = value
        obj.description = description
        obj.longitude = longitude
        obj.latitude = latitude
        obj.save()

        if original_value != obj.value:
            Notification.objects.create(
                _('The value of the attribute [%s] has more than %d characters. '
                  'The original value is truncated: %s') % (
                    obj.value,
                    Attribute.VALUE_LEN,
                    original_value
                )
            )

        return obj

    @staticmethod
    def filter_by_prefix_value(tags):
        """
        tags = ['PR1-value1', 'PR2-value2', ...]
        """
        qs = []
        for tag in tags:
            try:
                prefix, value = tag.split('-', 1)
            except ValueError:
                continue

            qs.append(Q(property_att__prefix=prefix, value=value))

        if qs:
            # Take one Q object from the list
            query = qs.pop()

            # Or the Q object with the ones remaining in the list
            for item in qs:
                query |= item

            # Query the model
            return ServerAttribute.objects.filter(query)

        return None


# FIXME https://docs.djangoproject.com/en/1.8/ref/contrib/gis/
class Attribute(models.Model, MigasLink):
    VALUE_LEN = 250

    property_att = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        verbose_name=_("Property")
    )

    value = models.CharField(
        verbose_name=_("value"),
        max_length=VALUE_LEN
    )

    description = models.TextField(
        verbose_name=_("description"),
        null=True,
        blank=True
    )

    longitude = models.FloatField(
        verbose_name=_("longitude"),
        null=True,
        blank=True
    )

    latitude = models.FloatField(
        verbose_name=_("latitude"),
        null=True,
        blank=True
    )

    objects = AttributeManager()

    TOTAL_COMPUTER_QUERY = "SELECT DISTINCT COUNT(client_computer.id) \
        FROM client_computer, client_computer_sync_attributes \
        WHERE core_attribute.id=client_computer_sync_attributes.attribute_id \
        AND client_computer_sync_attributes.computer_id=client_computer.id"

    def __str__(self):
        if self.id == 1:  # special case (SET-All Systems)
            return self.value
        elif self.property_att.prefix == 'CID' and \
                settings.MIGASFREE_COMPUTER_SEARCH_FIELDS[0] != 'id':
            return f'{self.description} (CID-{self.value})'
        else:
            return f'{self.property_att.prefix}-{self.value}'

    def prefix_value(self):
        return self.__str__()

    def has_location(self):
        return self.longitude is not None and self.latitude is not None

    def total_computers(self, user=None):
        from ...client.models import Computer

        if user and not user.userprofile.is_view_all():
            queryset = Computer.productive.scope(user.userprofile).filter(sync_attributes__id=self.id)
        else:
            queryset = Computer.productive.filter(sync_attributes__id=self.id)

        return queryset.count()

    total_computers.admin_order_field = 'total_computers'
    total_computers.short_description = _('Total computers')

    def update_value(self, new_value):
        if self.value != new_value:
            self.value = new_value
            self.save()

    def update_description(self, new_value):
        if self.description != new_value:
            self.description = new_value
            self.save()

    def delete(self, using=None, keep_parents=False):
        # Not allowed delete attribute of basic properties
        if self.property_att.sort != 'basic':
            return super().delete(using, keep_parents)

    @staticmethod
    def _kind_normal(property_att, value):
        obj = Attribute.objects.create(property_att, value)
        return [obj.id]

    @staticmethod
    def _kind_list(property_att, value):
        attributes = []

        lst = value.split(',')
        for item in lst:
            item = item.replace('\n', '')
            if item:
                obj = Attribute.objects.create(property_att, item)
                attributes.append(obj.id)

        return attributes

    @staticmethod
    def _kind_by_side(property_att, value):
        attributes = []

        if property_att.sort == 'server':
            obj = Attribute.objects.create(property_att, '')
            attributes.append(obj.id)

        lst = value.split('.')
        pos = 0

        if property_att.kind == 'R':  # Adds right
            for item in lst:
                obj = Attribute.objects.create(property_att, value[pos:])
                attributes.append(obj.id)
                pos += len(item) + 1

        if property_att.kind == 'L':  # Adds left
            for item in lst:
                pos += len(item) + 1
                obj = Attribute.objects.create(
                    property_att, value[0:pos - 1]
                )
                attributes.append(obj.id)

        return attributes

    @staticmethod
    def _process_json_item(property_att, item):
        value = item.get('value', None)
        description = item.get('description', None)
        if value:
            obj = Attribute.objects.create(property_att, str(value), str(description) if description else None)
            return [obj.id]

        return []

    @staticmethod
    def _kind_json(property_att, value):
        try:
            content = json.loads(value)
        except ValueError:
            return []

        if type(content) == list:
            attributes = []
            for item in content:
                attributes.extend(Attribute._process_json_item(property_att, item))

            return attributes

        if type(content) == dict:
            return Attribute._process_json_item(property_att, content)

    @staticmethod
    def process_kind_property(property_att, value):
        if property_att.kind not in list(zip(*Property.KIND_CHOICES))[0]:
            return []

        if property_att.kind == 'N':  # Normal
            return Attribute._kind_normal(property_att, value)
        elif property_att.kind == '-':  # List
            return Attribute._kind_list(property_att, value)
        elif property_att.kind == 'R' or property_att.kind == 'L':
            return Attribute._kind_by_side(property_att, value)
        elif property_att.kind == 'J':  # JSON
            return Attribute._kind_json(property_att, value)

    class Meta:
        app_label = 'core'
        verbose_name = _('Attribute')
        verbose_name_plural = _('Attributes')
        unique_together = (('property_att', 'value'),)
        ordering = ['property_att__prefix', 'value']


class ServerAttributeManager(DomainAttributeManager):
    def scope(self, user):
        return super().scope(user).filter(property_att__sort='server')


class ServerAttribute(Attribute):  # tag
    objects = ServerAttributeManager()

    def update_computers(self, computers):
        self.tags.clear()
        for item in computers:
            self.tags.add(item)

        self.save()

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        proxy = True


class ClientAttributeManager(DomainAttributeManager):
    def scope(self, user):
        return super().scope(user).filter(
            Q(property_att__sort='client') |
            Q(property_att__sort='basic')
        )


class ClientAttribute(Attribute):
    objects = ClientAttributeManager()

    class Meta:
        verbose_name = _('Feature')
        verbose_name_plural = _('Features')
        proxy = True


class BasicAttributeManager(DomainAttributeManager):
    def scope(self, user):
        return super().scope(user).filter(property_att__sort='basic')


class BasicAttribute(Attribute):
    objects = BasicAttributeManager()

    @staticmethod
    def process(**kwargs):
        properties = dict(Property.objects.filter(
            enabled=True, sort='basic'
        ).values_list('prefix', 'id'))

        basic_attributes = []

        if 'SET' in properties.keys():
            obj = Attribute.objects.get(pk=1)  # special case (SET-All Systems)
            basic_attributes.append(obj.id)

        if 'CID' in properties.keys() and 'id' in kwargs:
            description = f'{kwargs["description"]}'
            obj, _ = Attribute.objects.get_or_create(
                property_att=Property.objects.get(pk=properties['CID']),
                value=str(kwargs['id']),
                defaults={'description': description}
            )
            obj.update_description(description)
            basic_attributes.append(obj.id)

        if 'PLT' in properties.keys() and 'platform' in kwargs:
            obj, _ = Attribute.objects.get_or_create(
                property_att=Property.objects.get(pk=properties['PLT']),
                value=kwargs['platform']
            )
            basic_attributes.append(obj.id)

        if 'IP' in properties.keys() and 'ip_address' in kwargs:
            obj, _ = Attribute.objects.get_or_create(
                property_att=Property.objects.get(pk=properties['IP']),
                value=kwargs['ip_address']
            )
            basic_attributes.append(obj.id)

        if 'PRJ' in properties.keys() and 'project' in kwargs:
            obj, _ = Attribute.objects.get_or_create(
                property_att=Property.objects.get(pk=properties['PRJ']),
                value=kwargs['project']
            )
            basic_attributes.append(obj.id)

        if 'USR' in properties.keys() and 'user' in kwargs:
            obj, _ = Attribute.objects.get_or_create(
                property_att=Property.objects.get(pk=properties['USR']),
                value=kwargs['user']
            )
            basic_attributes.append(obj.id)

        return basic_attributes

    class Meta:
        verbose_name = _('Basic Attribute')
        verbose_name_plural = _('Basic Attributes')
        proxy = True
