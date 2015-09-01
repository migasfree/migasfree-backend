# -*- coding: utf-8 -*-

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

from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from .property import Property


class AttributeManager(models.Manager):
    def create(self, property_att, value, description=None):
        """
        if value = "text~other", description = "other"
        """
        if '~' in value:
            value, description = value.split('~')

        queryset = Attribute.objects.filter(
            property_att=property_att, value=value
        )
        if queryset.exists():
            return queryset[0]

        attribute = Attribute()
        attribute.property_att = property_att
        attribute.value = value
        attribute.description = description
        attribute.save()

        return attribute

    @staticmethod
    def filter_by_prefix_value(tags):
        """
        tags = ['PR1-value1', 'PR2-value2', ...]
        """
        qs = []
        for tag in tags:
            try:
                prefix, value = tag.split('-', 1)
            except:
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


@python_2_unicode_compatible
class Attribute(models.Model):
    property_att = models.ForeignKey(
        Property,
        verbose_name=_("Property")
    )

    value = models.CharField(
        verbose_name=_("value"),
        max_length=250
    )

    description = models.TextField(
        verbose_name=_("description"),
        null=True,
        blank=True
    )

    objects = AttributeManager()

    def __str__(self):
        return '%s-%s' % (
            self.property_att.prefix,
            self.value,
        )

    def prefix_value(self):
        return self.__str__()

    def delete(self, *args, **kwargs):
        # Not allowed delete atributte of basic properties
        if self.property_att.sort != 'basic':
            super(Attribute, self).delete(*args, **kwargs)

    @staticmethod
    def process_kind_property(property_att, value):
        attributes = []
        try:
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

            if property_att.kind == "R":  # Adds right
                lst = value.split(".")
                pos = 0
                for item in lst:
                    obj = Attribute.objects.create(property_att, value[pos:])
                    attributes.append(obj.id)
                    pos += len(item) + 1

            if property_att.kind == "L":  # Adds left
                lst = value.split(".")
                pos = 0
                for item in lst:
                    pos += len(item) + 1
                    obj = Attribute.objects.create(
                        property_att, value[0:pos - 1]
                    )
                    attributes.append(obj.id)
        except:
            pass

        return attributes

    class Meta:
        app_label = 'core'
        verbose_name = _("Attribute")
        verbose_name_plural = _("Attributes")
        unique_together = (("property_att", "value"),)


class ServerAttributeManager(AttributeManager):
    def get_queryset(self):
        return super(ServerAttributeManager, self).get_queryset().filter(
            property_att__sort='server'
        )


class ServerAttribute(Attribute):  # tag
    objects = ServerAttributeManager()

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")
        proxy = True


class ClientAttributeManager(AttributeManager):
    def get_queryset(self):
        return super(ClientAttributeManager, self).get_queryset().filter(
            Q(property_att__sort='client') | Q(property_att__sort='basic')
        )


class ClientAttribute(Attribute):
    objects = ClientAttributeManager()

    class Meta:
        verbose_name = _("Feature")
        verbose_name_plural = _("Features")
        proxy = True


class BasicAttributeManager(AttributeManager):
    def get_queryset(self):
        return super(BasicAttributeManager, self).get_queryset().filter(
            property_att__sort='basic'
        )


class BasicAttribute(Attribute):
    objects = BasicAttributeManager()

    @staticmethod
    def process(**kwargs):
        properties = dict(Property.objects.filter(
            enabled=True, sort='basic'
        ).values_list('prefix', 'id'))

        att_id = []

        if 'SET' in properties.keys():
            obj = Attribute.objects.create(
                Property.objects.get(pk=properties['SET']),
                'All Systems'
            )
            att_id.append(obj.id)

        if 'CID' in properties.keys() and 'id' in kwargs:
            obj = Attribute.objects.create(
                Property.objects.get(pk=properties['CID']),
                str(kwargs['id'])
            )
            att_id.append(obj.id)

        if 'PLT' in properties.keys() and 'platform' in kwargs:
            obj = Attribute.objects.create(
                Property.objects.get(pk=properties['PLT']),
                kwargs['platform']
            )
            att_id.append(obj.id)

        if 'IP' in properties.keys() and 'ip_address' in kwargs:
            obj = Attribute.objects.create(
                Property.objects.get(pk=properties['IP']),
                kwargs['ip_address']
            )
            att_id.append(obj.id)

        if 'PRJ' in properties.keys() and 'project' in kwargs:
            obj = Attribute.objects.create(
                Property.objects.get(pk=properties['PRJ']),
                kwargs['project']
            )
            att_id.append(obj.id)

        if 'USR' in properties.keys() and 'user' in kwargs:
            obj = Attribute.objects.create(
                Property.objects.get(pk=properties['USR']),
                kwargs['user']
            )
            att_id.append(obj.id)

        return att_id


    class Meta:
        verbose_name = _("Basic Attribute")
        verbose_name_plural = _("Basic Attributes")
        proxy = True
