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
from django.db.models.signals import pre_delete, pre_save, m2m_changed
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils.translation import gettext, gettext_lazy as _

from ...utils import sort_depends
from . import Property, Attribute, MigasLink


class AttributeSetManager(models.Manager):
    def scope(self, user):
        qs = super().get_queryset()
        if not user.is_view_all():
            qs = qs.filter(
                included_attributes__in=user.get_attributes()
            ).distinct()

        return qs


# FIXME https://docs.djangoproject.com/en/1.8/ref/contrib/gis/
class AttributeSet(models.Model, MigasLink):
    name = models.CharField(
        verbose_name=_("name"),
        max_length=50,
        unique=True
    )

    description = models.TextField(
        verbose_name=_("description"),
        null=True,
        blank=True
    )

    enabled = models.BooleanField(
        verbose_name=_("enabled"),
        default=True,
    )

    included_attributes = models.ManyToManyField(
        Attribute,
        related_name='attributeset_included',
        blank=True,
        verbose_name=_("included attributes"),
    )

    excluded_attributes = models.ManyToManyField(
        Attribute,
        related_name='attributeset_excluded',
        blank=True,
        verbose_name=_("excluded attributes"),
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

    objects = AttributeSetManager()

    def get_summary(self):
        return '({}) {}'.format(
            gettext(self._meta.verbose_name),
            self.description
        )

    def __str__(self):
        return self.name

    def related_objects(self, model, user):
        """
        Returns Queryset with the related computers based in attributes
        """
        if model == 'computer':
            from ...client.models import Computer

            return Computer.productive.scope(user).filter(
                sync_attributes__in=self.included_attributes.all()
            ).exclude(
                sync_attributes__in=self.excluded_attributes.all()
            ).distinct()

        return None

    def clean(self):
        super().clean()

        if self.id:
            att_set = AttributeSet.objects.get(pk=self.id)
            if att_set.name != self.name and \
                    Attribute.objects.filter(
                        property_att=Property.objects.get(prefix='SET', sort='basic'),
                        value=self.name
                    ).exists():
                raise ValidationError(_('Duplicated name'))

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)

        Attribute.objects.get_or_create(
            property_att=Property.objects.get(prefix='SET', sort='basic'),
            value=self.name,
            defaults={'description': ''}
        )

    @staticmethod
    def sets_dependencies():
        sets = {}
        for item in AttributeSet.objects.filter(enabled=True):
            sets[item.id] = []

            for subset in item.included_attributes.filter(
                ~Q(value='All Systems')
            ).filter(
                property_att__prefix='SET'
            ).filter(
                ~Q(value=item.name)
            ):
                sets[item.id].append(AttributeSet.objects.get(name=subset.value).id)

            for subset in item.excluded_attributes.filter(
                ~Q(value='All Systems')
            ).filter(
                property_att__prefix='SET'
            ).filter(
                ~Q(value=item.name)
            ):
                sets[item.id].append(AttributeSet.objects.get(name=subset.value).id)

        return sets

    @staticmethod
    def process(attributes):
        property_set = Property.objects.get(prefix='SET', sort='basic')

        depends = AttributeSet.sets_dependencies()
        sets = []
        try:
            sets = sort_depends(depends)
        except ValueError:
            pass

        att_id = []
        for item in sets:
            for att_set in AttributeSet.objects.filter(
                id=item
            ).filter(
                Q(included_attributes__id__in=attributes)
            ).filter(
                ~Q(excluded_attributes__id__in=attributes)
            ).distinct():
                att = Attribute.objects.create(property_set, att_set.name)
                att_id.append(att.id)
                # IMPORTANT: appends attribute to attribute list
                attributes.append(att.id)

        return att_id

    class Meta:
        app_label = 'core'
        verbose_name = _('Attribute Set')
        verbose_name_plural = _('Attribute Sets')


@receiver(pre_save, sender=AttributeSet)
def pre_save_attribute_set(sender, instance, **kwargs):
    if instance.id:
        att_set = AttributeSet.objects.get(pk=instance.id)
        if instance.name != att_set.name:
            att = Attribute.objects.get(
                property_att=Property.objects.get(prefix='SET', sort='basic'),
                value=att_set.name
            )
            att.update_value(instance.name)


@receiver(pre_delete, sender=AttributeSet)
def pre_delete_attribute_set(sender, instance, **kwargs):
    Attribute.objects.filter(
        property_att=Property.objects.get(prefix='SET', sort='basic'),
        value=instance.name
    ).delete()


@receiver(m2m_changed, sender=AttributeSet.included_attributes.through)
@receiver(m2m_changed, sender=AttributeSet.excluded_attributes.through)
def prevent_circular_dependencies(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action != 'pre_add':
        return

    if not reverse:
        depends = AttributeSet.sets_dependencies()
        atts_id = [int(x) for x in pk_set]
        depends[instance.id] = list(AttributeSet.objects.filter(
            name__in=Attribute.objects.filter(
                id__in=atts_id,
                property_att__prefix='SET'
            ).values_list('value', flat=True)
        ).values_list('id', flat=True))

        try:
            sort_depends(depends)
        except ValueError as e:
            from ast import literal_eval

            depends = literal_eval(str(e))
            if instance.id in depends:
                del depends[instance.id]

            review = list(AttributeSet.objects.filter(
                id__in=list(depends.keys())
            ).values_list('name', flat=True))
            raise ValidationError(
                _('Review circular dependencies: %s') % ', '.join(review)
            )
