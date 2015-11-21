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
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from . import Property, Attribute


# FIXME https://docs.djangoproject.com/en/1.8/ref/contrib/gis/
@python_2_unicode_compatible
class SetOfAttributes(models.Model):
    name = models.CharField(
        verbose_name=_("name"),
        max_length=50
    )

    enabled = models.BooleanField(
        verbose_name=_("enabled"),
        default=True,
    )

    included_attributes = models.ManyToManyField(
        Attribute,
        blank=True,
        verbose_name=_("included")
    )

    excluded_attributes = models.ManyToManyField(
        Attribute,
        related_name="ExcludedAttributesGroup",
        blank=True,
        verbose_name=_("excluded")
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

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        Attribute.objects.get_or_create(
            property_att=Property.objects.get(prefix='SET', sort='basic'),
            value=self.name,
            defaults={'description': ''}
        )

        super(SetOfAttributes, self).save(*args, **kwargs)

    @staticmethod
    def item_at_index(lst, item, before=-1):
        try:
            id_before = lst.index(before)
        except:
            id_before = -1

        try:
            id_item = lst.index(item)
        except:
            id_item = -1

        if id_item == -1:
            if id_before == -1:
                lst.append(item)
            else:
                lst.insert(id_before, item)
        else:
            if id_before > -1:
                if id_before < id_item:
                    lst = lst[0:id_before] + lst[id_item:] \
                        + lst[id_before:id_item]

        return lst

    @staticmethod
    def get_sets():
        sets = []
        for item in SetOfAttributes.objects.filter(enabled=True):
            sets = SetOfAttributes.item_at_index(sets, item.id)

            for subset in item.included_attributes.filter(
                ~Q(property_att__sort='basic')
            ).filter(property_att__prefix='SET').filter(~Q(value=item.name)):
                sets = SetOfAttributes.item_at_index(
                    sets,
                    SetOfAttributes.objects.get(name=subset.value).id,
                    before=item.id
                )

            for subset in item.excluded_attributes.filter(
                ~Q(property_att__sort='basic')
            ).filter(property_att__prefix='SET').filter(~Q(value=item.name)):
                sets = SetOfAttributes.item_at_index(
                    sets,
                    SetOfAttributes.objects.get(name=subset.value).id,
                    before=item.id
                )

        return sets

    @staticmethod
    def process(attributes):
        property_set = Property.objects.get(prefix='SET', sort='basic')

        att_id = []
        for item in SetOfAttributes.get_sets():
            for soa in SetOfAttributes.objects.filter(id=item).filter(
                Q(included_attributes__id__in=attributes)
            ).filter(~Q(excluded_attributes__id__in=attributes)):
                att_id.append(
                    Attribute.objects.create(property_set, soa.name).id
                )

        return att_id

    class Meta:
        app_label = 'core'
        verbose_name = _("Set of Attributes")
        verbose_name_plural = _("Set of Attributes")
