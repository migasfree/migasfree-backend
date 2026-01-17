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

"""Software and hardware inventory functions."""

import logging

from ...client.tasks import update_software_inventory
from ...hardware.models import Node
from ...hardware.tasks import save_computer_hardware
from .. import errmfs
from .helpers import return_message

logger = logging.getLogger('migasfree')


def upload_computer_hardware(request, name, uuid, computer, data):
    """
    Upload and process computer hardware information.

    Deletes existing hardware nodes and queues a Celery task to save
    the new hardware data asynchronously.
    """
    cmd = 'upload_computer_hardware'

    try:
        hw_data = data.get(cmd)
        if not hw_data:
            logger.warning('No hardware data received for computer %s', computer.id)
            return return_message(cmd, errmfs.error(errmfs.GENERIC))

        # Handle list format (take first element)
        if isinstance(hw_data, list):
            hw_data = hw_data[0]

        # Clear existing hardware and queue async save
        Node.objects.filter(computer=computer).delete()
        save_computer_hardware.delay(computer.id, hw_data)

        # Update capture metadata
        computer.update_last_hardware_capture()
        computer.update_hardware_resume()

        logger.debug('Hardware upload queued for computer %s', computer.id)
        return return_message(cmd, errmfs.ok())

    except (IndexError, KeyError) as e:
        logger.error('Failed to upload hardware for computer %s: %s', computer.id, e)
        return return_message(cmd, errmfs.error(errmfs.GENERIC))


def upload_computer_software_base_diff(request, name, uuid, computer, data):
    """
    Upload software inventory diff.

    Processes a newline-separated list of packages (with +/- prefixes)
    and queues a Celery task to update the software inventory.
    """
    cmd = 'upload_computer_software_base_diff'

    try:
        raw_packages = data.get(cmd, '')
        if not raw_packages:
            return return_message(cmd, errmfs.ok())

        packages = raw_packages.split('\n')
        # Remove +/- prefix from each package
        clean_packages = [pkg[1:] for pkg in packages if pkg]

        update_software_inventory.delay(computer.id, clean_packages)

        logger.debug('Software inventory update queued for computer %s (%d packages)', computer.id, len(clean_packages))
        return return_message(cmd, errmfs.ok())

    except (IndexError, AttributeError) as e:
        logger.error('Failed to process software diff for computer %s: %s', computer.id, e)
        return return_message(cmd, errmfs.error(errmfs.GENERIC))


def upload_computer_software_base(request, name, uuid, computer, data):
    """
    DEPRECATED: Endpoint for migasfree-client >= 4.14.

    Kept for backward compatibility, returns success without processing.
    """
    return return_message('upload_computer_software_base', errmfs.ok())


def upload_computer_software_history(request, name, uuid, computer, data):
    """
    Upload software installation/removal history.

    Updates the computer's software history with the provided data.
    """
    cmd = 'upload_computer_software_history'

    try:
        history_data = data.get(cmd)
        if history_data:
            computer.update_software_history(history_data)
            logger.debug('Software history updated for computer %s', computer.id)
        return return_message(cmd, errmfs.ok())

    except (IndexError, KeyError) as e:
        logger.error('Failed to update software history for computer %s: %s', computer.id, e)
        return return_message(cmd, errmfs.error(errmfs.GENERIC))


def get_computer_software(request, name, uuid, computer, data):
    """
    DEPRECATED: Endpoint for migasfree-client >= 4.14.

    Previously returned computer.version.base, now returns empty string
    for backward compatibility.
    """
    return return_message('get_computer_software', '')
