# -*- coding: utf-8 -*-

# Copyright (c) 2015-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2021 Alberto Gacías <alberto@migasfree.org>
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

from django.db import models
from django.db.models import Q
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .migas_link import MigasLink
from .property import Property


class DomainAttributeManager(models.Manager):
    def scope(self, user):
        qs = super().get_queryset()
        if not user.is_view_all():
            qs = qs.filter(
                Q(id__in=user.get_attributes()) |
                Q(id__in=user.get_domain_tags())
            )

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
        else:
            description = description

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
            return '{} (CID-{})'.format(self.description, self.value)
        else:
            return '{}-{}'.format(self.property_att.prefix, self.value)

    def prefix_value(self):
        return self.__str__()

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
    def process_kind_property(property_att, value):
        attributes = []

        if property_att.kind == "N":  # Normal
            obj = Attribute.objects.create(property_att, value)
            attributes.append(obj.id)

        if property_att.kind == "-":  # List
            lst = value.split(",")
            for item in lst:
                item = item.replace('\n', '')
                if item:
                    obj = Attribute.objects.create(property_att, item)
                    attributes.append(obj.id)

        if property_att.kind == "R" or property_att.kind == "L":
            if property_att.sort == 'server':
                obj = Attribute.objects.create(property_att, '')
                attributes.append(obj.id)

            lst = value.split(".")
            pos = 0

            if property_att.kind == "R":  # Adds right
                for item in lst:
                    obj = Attribute.objects.create(property_att, value[pos:])
                    attributes.append(obj.id)
                    pos += len(item) + 1

            if property_att.kind == "L":  # Adds left
                for item in lst:
                    pos += len(item) + 1
                    obj = Attribute.objects.create(
                        property_att, value[0:pos - 1]
                    )
                    attributes.append(obj.id)

        return attributes

    class Meta:
        app_label = 'core'
        verbose_name = _('Attribute')
        verbose_name_plural = _('Attributes')
        unique_together = (("property_att", "value"),)
        ordering = ['property_att__prefix', 'value']


class ServerAttributeManager(DomainAttributeManager):
    def scope(self, user):
        qs = super().scope(user)

        return qs.filter(property_att__sort='server')


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
        qs = super().scope(user)

        return qs.filter(
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
        qs = super().scope(user)

        return qs.filter(property_att__sort='basic')


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
            description = '{}'.format(kwargs['description'])
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
