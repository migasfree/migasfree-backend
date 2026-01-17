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

"""Faults and errors handling functions."""

import logging

from ...client.models import Error, Fault, FaultDefinition
from .. import errmfs
from .helpers import return_message

logger = logging.getLogger('migasfree')


def upload_computer_errors(request, name, uuid, computer, data):
    """
    Upload and store computer errors.

    Creates an Error record for the computer with the provided error data.
    """
    cmd = 'upload_computer_errors'

    try:
        error_data = data.get(cmd)
        if error_data:
            Error.objects.create(computer, computer.project, error_data)
            logger.debug('Error recorded for computer %s', computer.id)
        return return_message(cmd, errmfs.ok())
    except (IndexError, KeyError) as e:
        logger.error('Failed to upload computer error: %s', e)
        return return_message(cmd, errmfs.error(errmfs.GENERIC))


def upload_computer_faults(request, name, uuid, computer, data):
    """
    Upload and store computer faults.

    Processes fault results from the client and creates Fault records
    for any faults that have non-empty results (indicating a problem).

    Input format:
        {
            'upload_computer_faults': {
                'faults': {
                    'fault_name': 'result',
                    ...
                }
            }
        }
    """
    cmd = 'upload_computer_faults'

    try:
        faults_data = data.get(cmd, {}).get('faults', {})

        if not faults_data:
            logger.debug('No faults data received for computer %s', computer.id)
            return return_message(cmd, {})

        # Prefetch fault definitions to avoid N+1 queries
        fault_names = list(faults_data.keys())
        fault_definitions = {fd.name: fd for fd in FaultDefinition.objects.filter(name__in=fault_names)}

        faults_created = 0
        for fault_name, result in faults_data.items():
            if not result:  # No fault detected
                continue

            fault_def = fault_definitions.get(fault_name)
            if fault_def:
                Fault.objects.create(computer, fault_def, result)
                faults_created += 1
            else:
                logger.warning('Fault definition not found: %s (computer: %s)', fault_name, computer.id)

        logger.debug('Uploaded %d faults for computer %s', faults_created, computer.id)
        return return_message(cmd, {})

    except AttributeError as e:
        logger.error('Invalid faults data structure: %s', e)
        return return_message(cmd, errmfs.error(errmfs.GENERIC))
