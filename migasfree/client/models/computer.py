# -*- coding: utf-8 -*-

# Copyright (c) 2015-2016 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2016 Alberto Gacías <alberto@migasfree.org>
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

from datetime import datetime

from django.db import models, transaction
from django.db.models import Count
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext, ugettext_lazy as _
from django.template import Context, Template
from django.conf import settings

from migasfree.utils import swap_m2m, remove_empty_elements_from_dict
from migasfree.core.models import (
    Project, ServerAttribute, Attribute, BasicProperty
)

from .package import Package
from .user import User


class ProductiveManager(models.Manager):
    def get_queryset(self):
        return super(ProductiveManager, self).get_queryset().filter(
            status__in=Computer.PRODUCTIVE_STATUS
        )


class UnproductiveManager(models.Manager):
    def get_queryset(self):
        return super(UnproductiveManager, self).get_queryset().exclude(
            status__in=Computer.PRODUCTIVE_STATUS
        )


class SubscribedManager(models.Manager):
    def get_queryset(self):
        return super(SubscribedManager, self).get_queryset().exclude(
            status='unsubscribed'
        )


class UnsubscribedManager(models.Manager):
    def get_queryset(self):
        return super(UnsubscribedManager, self).get_queryset().filter(
            status='unsubscribed'
        )


@python_2_unicode_compatible
class Computer(models.Model):
    STATUS_CHOICES = (
        ('intended', _('Intended')),
        ('reserved', _('Reserved')),
        ('unknown', _('Unknown')),
        ('in repair', _('In repair')),
        ('available', _('Available')),
        ('unsubscribed', _('Unsubscribed')),
    )

    PRODUCTIVE_STATUS = ['intended', 'reserved', 'unknown']

    MACHINE_CHOICES = (
        ('P', _('Physical')),
        ('V', _('Virtual')),
    )

    uuid = models.CharField(
        verbose_name=_("uuid"),
        max_length=36,
        null=True,
        blank=True,
        unique=True,
        default=""
    )

    status = models.CharField(
        verbose_name=_('status'),
        max_length=20,
        null=False,
        choices=STATUS_CHOICES,
        default=settings.MIGASFREE_DEFAULT_COMPUTER_STATUS
    )

    name = models.CharField(
        verbose_name=_("name"),
        max_length=50,
        null=True,
        blank=True,
        unique=False
    )

    project = models.ForeignKey(
        Project,
        verbose_name=_("project")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    ip_address = models.GenericIPAddressField(
        verbose_name=_("ip address"),
        null=True,
        blank=True
    )

    software_inventory = models.ManyToManyField(
        Package,
        blank=True,
        verbose_name=_("software inventory"),
    )

    software_history = models.TextField(
        verbose_name=_("software history"),
        default="",
        null=True,
        blank=True
    )

    logical_devices_assigned = models.ManyToManyField(
        # http://python.6.x6.nabble.com/many-to-many-between-apps-td5026629.html
        'device.Logical',
        blank=True,
        verbose_name=_("logical devices assigned"),
        related_name='logical_devices_assigned',
    )

    logical_devices_installed = models.ManyToManyField(
        'device.Logical',
        blank=True,
        verbose_name=_("logical devices installed"),
        related_name='logical_devices_installed',
        editable=False,
    )

    last_hardware_capture = models.DateTimeField(
        verbose_name=_("last hardware capture"),
        null=True,
        blank=True,
    )

    tags = models.ManyToManyField(
        ServerAttribute,
        blank=True,
        verbose_name=_("tags"),
        related_name='tags'
    )

    sync_start_date = models.DateTimeField(
        verbose_name=_('sync start date'),
        null=True,
    )

    sync_end_date = models.DateTimeField(
        verbose_name=_("sync end date"),
        null=True,
    )

    sync_user = models.ForeignKey(
        User,
        verbose_name=_("sync user"),
        null=True,
    )

    sync_attributes = models.ManyToManyField(
        Attribute,
        blank=True,
        verbose_name=_("sync attributes"),
        help_text=_("attributes sent")
    )

    product = models.CharField(
        verbose_name=_("product"),
        max_length=80,
        null=True,
        blank=True,
        unique=False
    )

    machine = models.CharField(
        verbose_name=_("machine"),
        max_length=1,
        null=False,
        choices=MACHINE_CHOICES,
        default='P'
    )

    cpu = models.CharField(
        verbose_name=_("CPU"),
        max_length=50,
        null=True,
        blank=True,
        unique=False
    )

    ram = models.BigIntegerField(
        verbose_name=_("RAM"),
        null=True,
        blank=True
    )

    storage = models.BigIntegerField(
        verbose_name=_("storage"),
        null=True,
        blank=True
    )

    disks = models.SmallIntegerField(
        verbose_name=_("disks"),
        null=True,
        blank=True
    )

    mac_address = models.CharField(
        verbose_name=_("MAC address"),
        max_length=60,  # size for 5
        null=True,
        blank=True,
        unique=False
    )

    objects = models.Manager()
    productives = ProductiveManager()
    unproductives = UnproductiveManager()
    subscribed = SubscribedManager()
    unsubscribed = UnsubscribedManager()

    def __init__(self, *args, **kwargs):
        super(Computer, self).__init__(*args, **kwargs)

        if not settings.MIGASFREE_REMOTE_ADMIN_LINK:
            self._actions = None
            return

        self._actions = []
        template = Template(' '.join(settings.MIGASFREE_REMOTE_ADMIN_LINK))
        context = {'computer': self}
        for node in template.nodelist:
            try:
                token = node.filter_expression.token
                if not token.startswith('computer'):
                    context[token] = ','.join(list(
                        self.sync_attributes.filter(
                            property_att__prefix=token
                        ).values_list('value', flat=True)
                    ))
            except:
                pass

        remote_admin = template.render(Context(context))

        for element in remote_admin.split(' '):
            protocol = element.split('://')[0]
            self._actions.append([protocol, element])

    def get_all_attributes(self):
        return list(self.tags.values_list('id', flat=True)) \
            + list(self.sync_attributes.values_list('id', flat=True))

    def login(self):
        return u'%s (%s)' % (
            self.sync_user.name,
            self.sync_user.fullname.strip()
        )

    def hardware(self):
        try:
            return self.node_set.get(computer=self.id, parent=None).__str__()
        except:
            return ''

    def change_status(self, status):
        if status not in list(dict(self.STATUS_CHOICES).keys()):
            return False

        self.status = status
        self.save()

        return True

    def update_software_history(self, history):
        if history:
            if self.software_history:
                self.software_history = history + '\n\n' + self.software_history
            else:
                self.software_history = history
            self.save()

    @staticmethod
    def group_by_project():
        return Computer.productives.values(
            'project__name', 'project__id'
        ).annotate(count=Count('id'))

    @staticmethod
    def group_by_platform():
        return Computer.productives.values(
            'project__platform__name', 'project__platform__id'
        ).annotate(count=Count('id'))

    @staticmethod
    def count_by_attributes(attributes_id, project_id=None):
        if project_id:
            return Computer.objects.filter(
                sync_attributes__id__in=attributes_id,
                project__id=project_id
            ).count()
        else:
            return Computer.objects.filter(
                sync_attributes__id__in=attributes_id
            ).count()

    @transaction.atomic
    def update_software_inventory(self, pkgs):
        if pkgs:
            self.software_inventory.clear()
            self.software_inventory = pkgs
            self.save()

    def update_last_hardware_capture(self):
        self.last_hardware_capture = datetime.now()
        self.save()

    def update_hardware_resume(self):
        from migasfree.hardware.models import Node

        try:
            self.product = Node.objects.get(
                computer=self.id, parent=None
            ).get_product()
        except:
            self.product = None

        self.machine = 'V' if Node.get_is_vm(self.id) else 'P'
        self.cpu = Node.get_cpu(self.id)
        self.ram = Node.get_ram(self.id)
        self.disks, self.storage = Node.get_storage(self.id)
        self.mac_address = Node.get_mac_address(self.id)

        self.save()

    @staticmethod
    def replacement(source, target):
        swap_m2m(source.tags, target.tags)
        swap_m2m(source.logical_devices_assigned, target.logical_devices_assigned)

        source_cid = source.get_cid_attribute()
        target_cid = target.get_cid_attribute()
        swap_m2m(source_cid.faultdefinition_set, target_cid.faultdefinition_set)
        swap_m2m(source_cid.deployment_set, target_cid.deployment_set)
        swap_m2m(source_cid.ExcludeAttribute, target_cid.ExcludeAttribute)
        swap_m2m(source_cid.setofattributes_set, target_cid.setofattributes_set)
        swap_m2m(
            source_cid.ExcludedAttributesGroup,
            target_cid.ExcludedAttributesGroup
        )
        swap_m2m(source_cid.delays, target_cid.delays)

        source.status, target.status = target.status, source.status

        source.save()
        target.save()

    def get_cid_attribute(self):
        prop = BasicProperty.objects.get(prefix='CID')
        cid_att, _ = Attribute.objects.get_or_create(
            property_att=prop,
            value=str(self.id),
            defaults={'description': self.get_cid_description()}
        )

        return cid_att

    def get_cid_description(self):
        desc = list(settings.MIGASFREE_COMPUTER_SEARCH_FIELDS)
        if 'id' in desc:
            desc.remove('id')

        return str(self.__getattribute__(desc[0]))

    def get_replacement_info(self):
        cid = self.get_cid_attribute()

        return remove_empty_elements_from_dict({
            ugettext("Computer"): self.__str__(),
            ugettext("Status"): ugettext(self.status),
            ugettext("Tags"): ', '.join(str(x) for x in self.tags.all()),
            ugettext("Faults"): ', '.join(
                str(x) for x in cid.faultdefinition_set.all()
            ),
            ugettext("Deployments"): ', '.join(
                str(x) for x in cid.deployment_set.all()
            ),
            ugettext("Deployments (excluded)"): ', '.join(
                str(x) for x in cid.ExcludeAttribute.all()
            ),
            ugettext("Sets"): ', '.join(
                str(x) for x in cid.setofattributes_set.all()
            ),
            ugettext("Sets (excluded)"): ', '.join(
                str(x) for x in cid.ExcludedAttributesGroup.all()
            ),
            ugettext("Delays"): ', '.join(
                str(x) for x in cid.delays.all()
            ),
            ugettext("Devices"): ', '.join(
                str(x) for x in self.logical_devices_assigned.all()
            ),
        })

    def __str__(self):
        if settings.MIGASFREE_COMPUTER_SEARCH_FIELDS[0] == "id":
            return 'CID-%d' % self.id
        else:
            return '%s (CID-%d)' % (self.get_cid_description(), self.id)

    class Meta:
        app_label = 'client'
        verbose_name = _("Computer")
        verbose_name_plural = _("Computers")


from .status_log import StatusLog


@receiver(pre_save, sender=Computer)
def pre_save_computer(sender, instance, **kwargs):
    if instance.id:
        old_obj = Computer.objects.get(pk=instance.id)
        if old_obj.status != instance.status:
            StatusLog.objects.create(instance)


@receiver(post_save, sender=Computer)
def post_save_computer(sender, instance, created, **kwargs):
    if created:
        StatusLog.objects.create(instance)

    if instance.status in ['available', 'unsubscribed']:
        instance.tags.clear()
        instance.logical_devices_assigned.clear()

        cid = instance.get_cid_attribute()
        cid.faultdefinition_set.clear()
        cid.deployment_set.clear()
        cid.ExcludeAttribute.clear()
        cid.setofattributes_set.clear()
        cid.ExcludedAttributesGroup.clear()
        cid.delays.clear()
