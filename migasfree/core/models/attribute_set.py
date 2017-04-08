# -*- coding: utf-8 -*-

# Copyright (c) 2015-2017 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2017 Alberto Gacías <alberto@migasfree.org>
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
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver

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

    def clean(self):
        super(SetOfAttributes, self).clean()

        if self.id:
            soa = SetOfAttributes.objects.get(pk=self.id)
            if soa.name != self.name and \
                    Attribute.objects.filter(
                        property_att=Property(prefix='SET', sort='basic'), value=self.name
                    ).count() > 0:
                raise ValidationError(_('Duplicated name'))

    def save(self, *args, **kwargs):
        super(SetOfAttributes, self).save(*args, **kwargs)

        Attribute.objects.get_or_create(
            property_att=Property.objects.get(prefix='SET', sort='basic'),
            value=self.name,
            defaults={'description': ''}
        )

    @staticmethod
    def item_at_index(lst, item, before=-1):
        try:
            id_before = lst.index(before)
        except ValueError:
            id_before = -1

        try:
            id_item = lst.index(item)
        except ValueError:
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
                att = Attribute.objects.create(property_set, soa.name)
                att_id.append(att.id)
                attributes.append(att.id)

        return att_id

    class Meta:
        app_label = 'core'
        verbose_name = _("Set of Attributes")
        verbose_name_plural = _("Set of Attributes")


@receiver(pre_save, sender=SetOfAttributes)
def pre_save_set_of_attributes(sender, instance, **kwargs):
    if instance.id:
        soa = SetOfAttributes.objects.get(pk=instance.id)
        if instance.name != soa.name:
            att = Attribute.objects.get(property_att=Property(prefix='SET', sort='basic'), value=soa.name)
            att.update_value(instance.name)


@receiver(pre_delete, sender=SetOfAttributes)
def pre_delete_set_of_attributes(sender, instance, **kwargs):
    try:
        Attribute.objects.get(property_att=Property(prefix='SET', sort='basic'), value=instance.name).delete()
    except ObjectDoesNotExist:
        pass
