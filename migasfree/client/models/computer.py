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

from datetime import datetime

from django.db import models
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.template import Context, Template
from django.conf import settings

from migasfree.core.models import Project, ServerAttribute, Attribute

from .package import Package
from .user import User


@python_2_unicode_compatible
class Computer(models.Model):
    STATUS_CHOICES = (
        ('intended', _('Intended')),
        ('available', _('Available')),
        ('reserved', _('Reserved')),
        ('unsubscribed', _('Unsubscribed')),
        ('unknown', _('Unknown')),
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
        default='intended'
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
        null=True,
        blank=True,
        verbose_name=_("software inventory"),
    )

    software_history = models.TextField(
        verbose_name=_("software history"),
        default="",
        null=True,
        blank=True
    )

    #TODO
    '''
    logical_devices = models.ManyToManyField(
        # http://python.6.x6.nabble.com/many-to-many-between-apps-td5026629.html
        'device.Logical',
        null=True,
        blank=True,
        verbose_name=_("logical devices"),
    )
    '''

    logical_devices_copy = models.TextField(
        verbose_name=_("logical devices copy"),
        null=True,
        blank=False,
        editable=False
    )

    last_hardware_capture = models.DateTimeField(
        verbose_name=_("last hardware capture"),
        null=True,
        blank=True,
    )

    tags = models.ManyToManyField(
        ServerAttribute,
        null=True,
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
        null=True,
        blank=True,
        verbose_name=_("sync attributes"),
        help_text=_("attributes sent")
    )

    def __init__(self, *args, **kwargs):
        super(Computer, self).__init__(*args, **kwargs)

        if settings.MIGASFREE_REMOTE_ADMIN_LINK == '' \
        or settings.MIGASFREE_REMOTE_ADMIN_LINK is None:
            self._actions = None

        self._actions = []
        _template = Template(settings.MIGASFREE_REMOTE_ADMIN_LINK)
        _context = {"computer": self}
        for n in _template.nodelist:
            try:
                _token = n.filter_expression.token
                if not _token.startswith("computer"):
                    _context[_token] = self.login().attributes.get(
                        property_att__prefix=_token
                    ).value
            except:
                pass
        _remote_admin = _template.render(Context(_context))

        for element in _remote_admin.split(" "):
            protocol = element.split("://")[0]
            self._actions.append([protocol, element])

    def get_all_attributes(self):
        return list(self.tags.values_list('id', flat=True)) \
            + list(self.sync_attributes.values_list('id', flat=True))

    def remove_device_copy(self, logical_id):
        try:
            lst = self.devices_copy.split(',')
            if logical_id in lst:
                lst.remove(logical_id)
                self.devices_copy = ','.join(lst)
                self.save()
        except:
            pass

    def append_device_copy(self, logical_id):
        try:
            lst = self.devices_copy.split(',')
            if logical_id not in lst:
                lst.append(logical_id)
                self.devices_copy = ','.join(lst)
                self.save()
        except:
            pass

    def login(self):
        return '%s@%s' % (
            self.sync_user.name,
            self.computer.__str__()
        )

    def change_status(self, status):
        if status not in dict(self.STATUS_CHOICES).keys():
            return False

        self.status = status
        self.save()

        return True

    def update_software_history(self, history):
        if history:
            self.software_history = history + '\n\n' + self.software_history
            self.save()

    def update_software_inventory(self, inventory):
        if inventory and type(inventory) == list:
            pkgs = []
            new_pkgs = []
            for package in inventory:
                if package:
                    # name_version_architecture.ext convention
                    try:
                        name, version, architecture = package.split('_')
                    except:
                        continue
                    architecture = architecture.split('.')[0]
                    try:
                        pkgs.append(Package.objects.get(
                            fullname=package, project__id=self.project.id
                        ))
                    except:
                        new_pkgs.append(
                            Package(
                                fullname=package,
                                name=name, version=version,
                                architecture=architecture, project=self.project
                            )
                        )

            if new_pkgs:
                bulk = Package.objects.bulk_create(new_pkgs)
                objs = Package.objects.filter(fullname__in=bulk)
                [pkgs.append(x) for x in objs]

            self.software_inventory.clear()
            self.software_inventory = pkgs
            self.save()

    @staticmethod
    def replacement(source, target):
        source.tags, target.tags = target.tags, source.tags
        source.status, target.status = target.status, source.status

        source.save()
        target.save()

    def __str__(self):
        return str(self.__getattribute__(
            settings.MIGASFREE_COMPUTER_SEARCH_FIELDS[0]
        ))

    def save(self, *args, **kwargs):
        if 'available' == self.status:
            self.tags.clear()

        super(Computer, self).save(*args, **kwargs)

    class Meta:
        app_label = 'client'
        verbose_name = _("Computer")
        verbose_name_plural = _("Computers")

#TODO
'''
@receiver(m2m_changed, sender=Computer.logical_devices.through)
def computers_changed(sender, **kwargs):
    if kwargs['action'] == 'post_add':
        for computer in Computer.objects.filter(pk__in=kwargs['pk_set']):
            computer.remove_device_copy(kwargs['instance'].id)
'''
