# -*- coding: utf-8 -*-

# Copyright (c) 2015-2019 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2019 Alberto Gacías <alberto@migasfree.org>
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

from django.db import models
from django.db.models import Count
from django.db.models.functions import ExtractMonth, ExtractYear
from django.db.models.signals import pre_save, post_save, pre_delete
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext, ugettext_lazy as _
from django.conf import settings

from migasfree.utils import swap_m2m, remove_empty_elements_from_dict, list_difference
from migasfree.core.models import (
    Project, ServerAttribute, Attribute, BasicProperty, Property,
)
from migasfree.device.models import Logical

from .user import User


class DomainComputerManager(models.Manager):
    def scope(self, user):
        qs = super(DomainComputerManager, self).get_queryset()
        if not user.is_view_all():
            qs = qs.filter(id__in=user.get_computers())

        return qs


class ProductiveManager(DomainComputerManager):
    def get_queryset(self):
        return super(ProductiveManager, self).get_queryset().filter(
            status__in=Computer.PRODUCTIVE_STATUS
        )

    def scope(self, user):
        return super(ProductiveManager, self).scope(user).filter(
            status__in=Computer.PRODUCTIVE_STATUS
        )


class UnproductiveManager(DomainComputerManager):
    def get_queryset(self):
        return super(UnproductiveManager, self).get_queryset().exclude(
            status__in=Computer.PRODUCTIVE_STATUS
        )

    def scope(self, user):
        return super(UnproductiveManager, self).scope(user).exclude(
            status__in=Computer.PRODUCTIVE_STATUS
        )


class SubscribedManager(DomainComputerManager):
    def get_queryset(self):
        return super(SubscribedManager, self).get_queryset().exclude(
            status='unsubscribed'
        )

    def scope(self, user):
        return super(SubscribedManager, self).scope(user).exclude(
            status='unsubscribed'
        )


class UnsubscribedManager(DomainComputerManager):
    def get_queryset(self):
        return super(UnsubscribedManager, self).get_queryset().filter(
            status='unsubscribed'
        )

    def scope(self, user):
        return super(UnsubscribedManager, self).scope(user).filter(
            status='unsubscribed'
        )


class ActiveManager(DomainComputerManager):
    def get_queryset(self):
        return super(ActiveManager, self).get_queryset().filter(
            status__in=Computer.ACTIVE_STATUS
        )

    def scope(self, user):
        return super(ActiveManager, self).scope(user).filter(
            status__in=Computer.ACTIVE_STATUS
        )


class InactiveManager(DomainComputerManager):
    def get_queryset(self):
        return super(InactiveManager, self).get_queryset().exclude(
            status__in=Computer.ACTIVE_STATUS
        )

    def scope(self, user):
        return super(InactiveManager, self).scope(user).exclude(
            status__in=Computer.ACTIVE_STATUS
        )


class ComputerManager(DomainComputerManager):
    def create(self, name, project, uuid, ip_address=None, forwarded_ip_address=None):
        obj = Computer()
        obj.name = name
        obj.project = project
        obj.uuid = uuid
        obj.ip_address = ip_address
        obj.forwarded_ip_address = forwarded_ip_address
        obj.save()

        return obj


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
    ACTIVE_STATUS = PRODUCTIVE_STATUS + ['in repair']
    UNSUBSCRIBED_STATUS = ['unsubscribed']

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

    fqdn = models.CharField(
        verbose_name=_('full qualified domain name'),
        max_length=255,
        null=True,
        blank=True,
        unique=False
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_("project")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('entry date'),
        help_text=_('Date of entry into the migasfree system')
    )
    updated_at = models.DateTimeField(auto_now=True)

    ip_address = models.GenericIPAddressField(
        verbose_name=_("ip address"),
        null=True,
        blank=True
    )

    forwarded_ip_address = models.GenericIPAddressField(
        verbose_name=_("forwarded ip address"),
        null=True,
        blank=True
    )

    default_logical_device = models.ForeignKey(
        Logical,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("default logical device")
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
        on_delete=models.CASCADE,
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

    comment = models.TextField(
        verbose_name=_("comment"),
        null=True,
        blank=True
    )

    objects = ComputerManager()
    productive = ProductiveManager()
    unproductive = UnproductiveManager()
    subscribed = SubscribedManager()
    unsubscribed = UnsubscribedManager()
    active = ActiveManager()
    inactive = InactiveManager()

    @classmethod
    def stacked_by_month(cls, user, start_date, field='project_id'):
        return list(cls.objects.scope(user).filter(
            created_at__gte=start_date
        ).annotate(
            year=ExtractYear('created_at'),
            month=ExtractMonth('created_at')
        ).order_by('year', 'month', field).values('year', 'month', field).annotate(
            count=Count('id')
        ))

    @classmethod
    def entry_year(cls, user):
        return list(
            cls.objects.scope(user).filter(
                machine='P'
            ).annotate(
                year=ExtractYear('created_at')
            ).values(
                'year'
            ).annotate(
                count=Count('id')
            ).order_by('year')
        )

    def get_all_attributes(self):
        return list(self.tags.values_list('id', flat=True)) \
            + list(self.sync_attributes.values_list('id', flat=True))

    def get_attribute_sets(self):
        return self.sync_attributes.filter(property_att__prefix='SET')

    def get_only_attributes(self):
        return self.sync_attributes.exclude(property_att__prefix='SET')

    def login(self):
        return u'{} ({})'.format(
            self.sync_user.name,
            self.sync_user.fullname.strip()
        )

    def hardware(self):
        try:
            return self.node_set.get(computer=self.id, parent=None).__str__()
        except ObjectDoesNotExist:
            return ''

    def change_status(self, status):
        if status not in list(dict(self.STATUS_CHOICES).keys()):
            return False

        self.status = status
        self.save()

        return True

    def update_sync_user(self, user):
        self.sync_user = user
        self.sync_start_date = datetime.now()
        self.save()

    def update_identification(self, name, fqdn, project, uuid, ip_address, forwarded_ip_address):
        self.name = name
        self.fqdn = fqdn
        self.project = project
        self.uuid = uuid
        self.ip_address = ip_address
        self.forwarded_ip_address = forwarded_ip_address
        self.save()

    def update_software_history(self, history):
        from .package_history import PackageHistory

        if history:
            if 'installed' in history:
                for pkg in PackageHistory.objects.filter(
                    computer__id=self.id,
                    package__fullname__in=history['installed']
                ):
                    pkg.install_date = datetime.now()
                    pkg.save()
            if 'uninstalled' in history:
                for pkg in PackageHistory.objects.filter(
                    computer__id=self.id,
                    package__fullname__in=history['uninstalled']
                ):
                    pkg.uninstall_date = datetime.now()
                    pkg.save()

    @staticmethod
    def group_by_project():
        return Computer.productive.values(
            'project__name', 'project__id'
        ).annotate(count=Count('id'))

    @staticmethod
    def group_by_platform():
        return Computer.productive.values(
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

    def update_last_hardware_capture(self):
        self.last_hardware_capture = datetime.now()
        self.save()

    def update_hardware_resume(self):
        from migasfree.hardware.models import Node

        try:
            self.product = Node.objects.get(
                computer=self.id, parent=None
            ).get_product()
        except ObjectDoesNotExist:
            self.product = None

        self.machine = 'V' if Node.get_is_vm(self.id) else 'P'
        self.cpu = Node.get_cpu(self.id)
        self.ram = Node.get_ram(self.id)
        self.disks, self.storage = Node.get_storage(self.id)
        self.mac_address = Node.get_mac_address(self.id)

        self.save()

    def update_logical_devices(self, devices):
        """
        :param devices: [id1, id2, id3, ...]
        :return: void
        """
        cid_attribute = self.get_cid_attribute()
        initial_logical_devices = list(
            self.assigned_logical_devices_to_cid().values_list('id', flat=True)
        )

        for pk in list_difference(devices, initial_logical_devices):
            Logical.objects.get(pk=pk).attributes.add(cid_attribute)

        for pk in list_difference(initial_logical_devices, devices):
            Logical.objects.get(pk=pk).attributes.remove(cid_attribute)

    def logical_devices(self, attributes=None):
        if not attributes:
            attributes = self.sync_attributes.values_list('id', flat=True)

        return Logical.objects.filter(
            attributes__in=attributes
        ).distinct()

    logical_devices.short_description = _('Logical Devices')

    def inflicted_logical_devices(self):
        return self.logical_devices().exclude(
            attributes__in=[self.get_cid_attribute().pk]
        )

    inflicted_logical_devices.short_description = _('Inflicted Logical Devices')

    def assigned_logical_devices_to_cid(self):
        return self.logical_devices().difference(self.inflicted_logical_devices())

    assigned_logical_devices_to_cid.short_description = _('Assigned Logical Devices to CID')

    def get_architecture(self):
        from migasfree.hardware.models.node import Node

        node = Node.objects.filter(
            computer=self.id,
            class_name='processor',
            width__gt=0
        ).first()

        if node:
            return node.width

        node = Node.objects.filter(
            computer=self.id,
            class_name='system',
            width__gt=0
        )

        return node.width if node else None

    def is_docker(self):
        from migasfree.hardware.models.node import Node

        return Node.get_is_docker(self.id)

    @staticmethod
    def replacement(source, target):
        swap_m2m(source.tags, target.tags)
        source.default_logical_device, target.default_logical_device = (
            target.default_logical_device, source.default_logical_device
        )

        # SWAP CID
        source_cid = source.get_cid_attribute()
        target_cid = target.get_cid_attribute()
        swap_m2m(source_cid.devicelogical_set, target_cid.devicelogical_set)
        swap_m2m(source_cid.faultdefinition_set, target_cid.faultdefinition_set)
        swap_m2m(source_cid.deployment_set, target_cid.deployment_set)
        swap_m2m(source_cid.ExcludeAttribute, target_cid.ExcludeAttribute)
        swap_m2m(source_cid.attributeset_set, target_cid.attributeset_set)
        swap_m2m(
            source_cid.ExcludedAttributesGroup,
            target_cid.ExcludedAttributesGroup
        )
        swap_m2m(source_cid.scheduledelay_set, target_cid.scheduledelay_set)
        swap_m2m(
            source_cid.PolicyIncludedAttributes,
            target_cid.PolicyIncludedAttributes
        )
        swap_m2m(
            source_cid.PolicyExcludedAttributes,
            target_cid.PolicyExcludedAttributes
        )
        swap_m2m(
            source_cid.PolicyGroupIncludedAttributes,
            target_cid.PolicyGroupIncludedAttributes
        )
        swap_m2m(
            source_cid.PolicyGroupExcludedAttributes,
            target_cid.PolicyGroupExcludedAttributes
        )
        swap_m2m(
            source_cid.ScopeIncludedAttribute,
            target_cid.ScopeIncludedAttribute
        )
        swap_m2m(
            source_cid.ScopeExcludedAttribute,
            target_cid.ScopeExcludedAttribute
        )
        swap_m2m(
            source_cid.DomainIncludedAttribute,
            target_cid.DomainIncludedAttribute
        )
        swap_m2m(
            source_cid.DomainExcludedAttribute,
            target_cid.DomainExcludedAttribute
        )

        source.status, target.status = target.status, source.status

        # finally save changes!!! (order is important)
        source.save()
        target.save()

    def get_cid_attribute(self):
        cid_att, _ = Attribute.objects.get_or_create(
            property_att=BasicProperty.objects.get(prefix='CID'),
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
                str(x) for x in cid.attributeset_set.all()
            ),
            ugettext("Sets (excluded)"): ', '.join(
                str(x) for x in cid.ExcludedAttributesGroup.all()
            ),
            ugettext("Delays"): ', '.join(
                str(x) for x in cid.scheduledelay_set.all()
            ),
            ugettext("Logical devices"): ', '.join(
                str(x) for x in self.logical_devices()
            ),
            ugettext("Default logical device"): self.default_logical_device.__str__(),
            ugettext("Policies (included)"): ', '.join(
                str(x) for x in cid.PolicyIncludedAttributes.all()
            ),
            ugettext("Policies (excluded)"): ', '.join(
                str(x) for x in cid.PolicyExcludedAttributes.all()
            ),
            ugettext("Policy Groups (included)"): ', '.join(
                str(x) for x in cid.PolicyGroupIncludedAttributes.all()
            ),
            ugettext("Policy Groups (excluded)"): ', '.join(
                str(x) for x in cid.PolicyGroupExcludedAttributes.all()
            ),
        })

    def append_devices(self, computer_id):
        try:
            target = Computer.objects.get(pk=computer_id)
            target.devices_logical.add(*self.devices_logical.all())
        except ObjectDoesNotExist:
            pass

    def __str__(self):
        if settings.MIGASFREE_COMPUTER_SEARCH_FIELDS[0] == 'id':
            return u'CID-{}'.format(self.id)
        else:
            return u'{} (CID-{})'.format(self.get_cid_description(), self.id)

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
        cid = instance.get_cid_attribute()
        cid.devicelogical_set.clear()
        cid.faultdefinition_set.clear()
        cid.deployment_set.clear()
        cid.ExcludeAttribute.clear()
        cid.attributeset_set.clear()
        cid.ExcludedAttributesGroup.clear()
        cid.scheduledelay_set.clear()


@receiver(pre_delete, sender=Computer)
def pre_delete_computer(sender, instance, **kwargs):
    Attribute.objects.filter(
        property_att=Property.objects.get(prefix='CID'),
        value=instance.id
    ).delete()
