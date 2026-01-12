# Copyright (c) 2018-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2018-2026 Alberto Gacías <alberto@migasfree.org>
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

from django.db import models, transaction
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _

from ...utils import list_difference
from . import Attribute, MigasLink, Property, ServerAttribute


class Domain(models.Model, MigasLink):
    name = models.CharField(
        max_length=50,
        verbose_name=_('name'),
        unique=True,
        db_comment='domain name',
    )

    comment = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('comment'),
        db_comment='domain comments',
    )

    included_attributes = models.ManyToManyField(
        Attribute,
        related_name='domain_included',
        blank=True,
        verbose_name=_('included attributes'),
    )

    excluded_attributes = models.ManyToManyField(
        Attribute,
        related_name='domain_excluded',
        blank=True,
        verbose_name=_('excluded attributes'),
    )

    tags = models.ManyToManyField(
        ServerAttribute,
        related_name='domain_tags',
        blank=True,
        verbose_name=_('tags'),
    )

    def __str__(self):
        return self.name

    @staticmethod
    def process(attributes):
        property_set, _ = Property.objects.get_or_create(
            prefix='DMN', sort='server', defaults={'name': 'DOMAIN', 'kind': 'L'}
        )

        att_id = []
        for item in Domain.objects.all():
            for att_domain in (
                Domain.objects.filter(id=item.id)
                .filter(Q(included_attributes__id__in=attributes))
                .filter(~Q(excluded_attributes__id__in=attributes))
                .distinct()
            ):
                att = Attribute.objects.create(property_set, att_domain.name)
                att_id.append(att.id)

        return att_id

    def get_tags(self):
        tags = [Attribute.objects.get(property_att__prefix='DMN', value=self.name)]
        for tag in Attribute.objects.filter(property_att__prefix='DMN', value__startswith=f'{self.name}.'):
            tags.append(tag)

        for tag in self.tags.all():
            tags.append(tag)

        return tags

    def get_domain_admins(self):
        return list(self.domains.values('id', 'username'))

    def update_domain_admins(self, users):
        """
        :param users: [id1, id2, id3, ...]
        :return: void
        """
        from .user_profile import UserProfile

        if self.id:
            initial_admins = list(self.domains.values_list('id', flat=True))

            for pk in list_difference(initial_admins, users):
                try:
                    user = UserProfile.objects.get(pk=pk)
                    user.domains.remove(self.id)
                except UserProfile.DoesNotExist:
                    pass

            for pk in list_difference(users, initial_admins):
                try:
                    user = UserProfile.objects.get(pk=pk)
                    user.domains.add(self.id)
                except UserProfile.DoesNotExist:
                    pass

    def related_objects(self, model, user):
        """
        Returns Queryset with the related computers based in attributes
        """
        if model != 'computer':
            return None

        from ...client.models import Computer

        return (
            Computer.productive.scope(user)
            .filter(sync_attributes__in=self.included_attributes.all())
            .exclude(sync_attributes__in=self.excluded_attributes.all())
            .distinct()
        )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.name = slugify(self.name).upper()
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    class Meta:
        app_label = 'core'
        verbose_name = _('Domain')
        verbose_name_plural = _('Domains')
        db_table_comment = 'groups of computers managed by different administrators'


@receiver(post_save, sender=Domain)
def set_m2m_domain(sender, instance, created, **kwargs):
    property_att, _ = Property.objects.get_or_create(
        prefix='DMN', sort='server', defaults={'name': 'DOMAIN', 'kind': 'L'}
    )

    att_dmn, _ = Attribute.objects.get_or_create(value=instance.name, description='', property_att=property_att)

    # Add the domain attribute
    transaction.on_commit(lambda: instance.included_attributes.add(att_dmn))
