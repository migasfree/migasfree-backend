# Copyright (c) 2015-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2026 Alberto Gacías <alberto@migasfree.org>
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

"""
Helper functions for safe views.
"""

import logging

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from ....utils import uuid_change_format
from ... import models

logger = logging.getLogger('migasfree')


def get_user_or_create(name, fullname, ip_address=None):
    user, created = models.User.objects.get_or_create(name=name, fullname=fullname)

    if created and ip_address:
        msg = _('User [%s] registered by IP [%s].') % (name, ip_address)
        models.Notification.objects.create(message=msg)

    return user


# TODO call when computer is updated
def is_computer_changed(computer, name, project, ip_address, uuid):
    # compatibility with client apiv4
    if not computer:
        computer = models.Computer.objects.create(name, project, uuid)
        models.Migration.objects.create(computer, project)

        if settings.MIGASFREE_NOTIFY_NEW_COMPUTER:
            models.Notification.objects.create(
                _('New Computer added id=[%s]: NAME=[%s] UUID=[%s]') % (computer.id, computer, computer.uuid)
            )
    # end compatibility with client apiv4

    if computer.project != project:
        models.PackageHistory.uninstall_computer_packages(computer.id)

        models.Migration.objects.create(computer=computer, project=project)
        computer.update_project(project)

    if settings.MIGASFREE_NOTIFY_CHANGE_NAME and (computer.name != name):
        msg = _('Computer id=[%s]: NAME [%s] changed by [%s]') % (computer.id, computer, name)
        models.Notification.objects.create(message=msg)
        computer.update_name(name)

    if settings.MIGASFREE_NOTIFY_CHANGE_IP and (computer.ip_address != ip_address):
        msg = _('Computer id=[%s]: IP [%s] changed by [%s]') % (computer.id, computer.ip_address, ip_address)
        models.Notification.objects.create(message=msg)
        computer.update_ip_address(ip_address)

    if settings.MIGASFREE_NOTIFY_CHANGE_UUID and (computer.uuid != uuid):
        msg = _('Computer id=[%s]: UUID [%s] changed by [%s]') % (computer.id, computer.uuid, uuid)
        models.Notification.objects.create(message=msg)
        computer.update_uuid(uuid)

    return computer


def get_computer(uuid, name):
    logger.debug('uuid: %s, name: %s', uuid, name)

    try:
        computer = models.Computer.objects.get(uuid=uuid)
        logger.debug('computer found by uuid')

        return computer
    except models.Computer.DoesNotExist:
        pass

    try:
        computer = models.Computer.objects.get(uuid=uuid_change_format(uuid))
        logger.debug('computer found by uuid (endian format changed)')

        return computer
    except models.Computer.DoesNotExist:
        pass

    computer = models.Computer.objects.filter(mac_address__icontains=uuid[-12:])
    if computer.count() == 1 and uuid[0:8] == '0' * 8:
        logger.debug('computer found by mac_address (in uuid format)')

        return computer.first()

    try:
        computer = models.Computer.objects.get(name=name)
        logger.debug('computer found by name')

        return computer
    except (models.Computer.DoesNotExist, models.Computer.MultipleObjectsReturned):
        return None
