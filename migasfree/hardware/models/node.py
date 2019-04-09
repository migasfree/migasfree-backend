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

import re

from past.builtins import basestring

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from migasfree.client.models import Computer


def validate_mac(mac):
    return isinstance(mac, basestring) and \
        len(mac) == 17 and \
        len(re.findall(r':', mac)) == 5


class DomainNodeManager(models.Manager):
    def scope(self, user):
        qs = super(DomainNodeManager, self).get_queryset()
        if not user.is_view_all():
            qs = qs.filter(computer_id__in=user.get_computers())

        return qs


class NodeManager(DomainNodeManager):
    def create(self, data):
        obj = Node(
            parent=data.get('parent'),
            computer=data.get('computer'),
            level=data.get('level'),
            width=data.get('width'),
            name=data.get('name'),
            class_name=data.get('class_name'),
            enabled=data.get('enabled', False),
            claimed=data.get('claimed', False),
            description=data.get('description'),
            vendor=data.get('vendor'),
            product=data.get('product'),
            version=data.get('version'),
            serial=data.get('serial'),
            bus_info=data.get('bus_info'),
            physid=data.get('physid'),
            slot=data.get('slot'),
            size=data.get('size'),
            capacity=data.get('capacity'),
            clock=data.get('clock'),
            dev=data.get('dev')
        )
        obj.save()

        return obj


@python_2_unicode_compatible
class Node(models.Model):
    # Detect Virtual Machine with lshw:
    # http://techglimpse.com/xen-kvm-virtualbox-vm-detection-command/
    VIRTUAL_MACHINES = {
        'innotek GmbH': 'virtualbox',
        'Red Hat': 'openstack',
        'Supermicro': 'kvm host',
        'Xen': 'xen',
        'Bochs': 'kvm',
        'VMware, Inc.': 'vmware'
    }

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_("parent"),
        related_name="child"
    )

    computer = models.ForeignKey(
        Computer,
        on_delete=models.CASCADE,
        verbose_name=_("computer")
    )

    level = models.IntegerField(verbose_name=_("level"))

    width = models.BigIntegerField(
        verbose_name=_("width"),
        null=True
    )

    name = models.TextField(
        verbose_name=_("id"),
        blank=True
    )  # This is the field "id" in lshw

    class_name = models.TextField(
        verbose_name=_("class"),
        blank=True
    )  # This is the field "class" in lshw

    enabled = models.BooleanField(
        verbose_name=_("enabled"),
        default=False,
    )

    claimed = models.BooleanField(
        verbose_name=_("claimed"),
        default=False,
    )

    description = models.TextField(
        verbose_name=_("description"),
        null=True,
        blank=True
    )

    vendor = models.TextField(
        verbose_name=_("vendor"),
        null=True,
        blank=True
    )

    product = models.TextField(
        verbose_name=_("product"),
        null=True,
        blank=True
    )

    version = models.TextField(
        verbose_name=_("version"),
        null=True,
        blank=True
    )

    serial = models.TextField(
        verbose_name=_("serial"),
        null=True,
        blank=True
    )

    bus_info = models.TextField(
        verbose_name=_("bus info"),
        null=True,
        blank=True
    )

    physid = models.TextField(
        verbose_name=_("physid"),
        null=True,
        blank=True
    )

    slot = models.TextField(
        verbose_name=_("slot"),
        null=True,
        blank=True
    )

    size = models.BigIntegerField(
        verbose_name=_("size"),
        null=True
    )

    capacity = models.BigIntegerField(
        verbose_name=_("capacity"),
        null=True
    )

    clock = models.BigIntegerField(
        verbose_name=_("clock"),
        null=True
    )

    dev = models.TextField(
        verbose_name=_("dev"),
        null=True,
        blank=True
    )

    objects = NodeManager()

    def get_product(self):
        if self.vendor:
            return self.VIRTUAL_MACHINES.get(self.vendor, self.product)
        if self.get_is_docker(self.computer_id):
            return "docker"

        return self.product or self.description

    def __str__(self):
        return self.get_product() or self.name

    @staticmethod
    def get_is_vm(computer_id):
        query = Node.objects.filter(
            computer=computer_id,
            parent_id__isnull=True
        )
        if query.count() == 1:
            if query[0].vendor in list(Node.VIRTUAL_MACHINES.keys()):
                return True
            elif Node.get_is_docker(computer_id):
                return True

        return False

    @staticmethod
    def get_is_docker(computer_id):
        query = Node.objects.filter(
            computer=computer_id,
            name="network",
            class_name="network",
            description="Ethernet interface"
        )

        return query.count() == 1 and \
            query[0].serial.upper().startswith("02:42:AC")

    @staticmethod
    def get_ram(computer_id):
        query = Node.objects.filter(
            computer=computer_id,
            name='memory',
            class_name='memory'
        )
        if query.count() == 1:
            size = query[0].size
        else:
            size = Node.objects.filter(
                computer=computer_id,
                class_name='memory',
                name__startswith='bank:'
            ).aggregate(
                models.Sum('size')
            )['size__sum']

        return size

    @staticmethod
    def get_cpu(computer_id):
        query = Node.objects.filter(
            computer=computer_id,
            class_name='processor'
        ).filter(
            models.Q(name='cpu') | models.Q(name='cpu:0')
        )
        if query.count() == 1:
            product = query[0].product
            if product:
                for item in ['(R)', '(TM)', '@', 'CPU']:
                    product = product.replace(item, '')
                return product.strip()
            else:
                return ''
        elif query.count() == 0:
            return ''
        else:
            return _('error')

    @staticmethod
    def get_mac_address(computer_id):
        """ returns all addresses in only string without any separator """
        query = Node.objects.filter(
            computer=computer_id,
            name__icontains='network',
            class_name='network'
        )
        lst = []
        for iface in query:
            if validate_mac(iface.serial):
                lst.append(iface.serial.upper().replace(':', ''))

        return ''.join(lst)

    @staticmethod
    def get_storage(computer_id):
        query = Node.objects.filter(
            computer=computer_id,
            name='disk',
            class_name='disk',
            size__gt=0
        )

        capacity = [item.size for item in query]

        return query.count(), sum(capacity)

    class Meta:
        app_label = 'hardware'
        verbose_name = _("Hardware Node")
        verbose_name_plural = _("Hardware Nodes")
