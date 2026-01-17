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
API v4 Functions - Backward compatibility module.

This file re-exports all functions from the refactored api/ package
to maintain backward compatibility with existing imports.

The actual implementations are now organized in:
    - api/helpers.py       - Notification and utility functions
    - api/computer.py      - Computer lookup and registration
    - api/sync.py          - Core sync (get_properties, upload_computer_info)
    - api/inventory.py     - Software/hardware inventory
    - api/faults.py        - Faults and errors handling
    - api/tags.py          - Computer tags management
    - api/packages.py      - Package upload functions
    - api/repositories.py  - Repository metadata creation
    - api/keys.py          - Packager keys
    - api/deprecated.py    - Deprecated endpoints
"""

# Re-export everything from the api package for backward compatibility
from .api import (  # noqa: I001
    # helpers
    add_notification_platform,
    add_notification_project,
    return_message,
    save_request_file,
    # computer
    get_computer,
    register_computer,
    # sync
    get_properties,
    upload_computer_info,
    upload_computer_message,
    # inventory
    upload_computer_hardware,
    upload_computer_software_base,
    upload_computer_software_base_diff,
    upload_computer_software_history,
    get_computer_software,
    # faults
    upload_computer_errors,
    upload_computer_faults,
    # tags
    get_computer_tags,
    set_computer_tags,
    # packages
    get_package_data,
    upload_server_package,
    upload_server_set,
    # repositories
    create_repositories_package,
    create_repositories_of_packageset,
    # keys
    get_key_packager,
    # deprecated
    upload_devices_changes,
)

__all__ = [
    'add_notification_platform',
    'add_notification_project',
    'create_repositories_of_packageset',
    'create_repositories_package',
    'get_computer',
    'get_computer_software',
    'get_computer_tags',
    'get_key_packager',
    'get_package_data',
    'get_properties',
    'register_computer',
    'return_message',
    'save_request_file',
    'set_computer_tags',
    'upload_computer_errors',
    'upload_computer_faults',
    'upload_computer_hardware',
    'upload_computer_info',
    'upload_computer_message',
    'upload_computer_software_base',
    'upload_computer_software_base_diff',
    'upload_computer_software_history',
    'upload_devices_changes',
    'upload_server_package',
    'upload_server_set',
]
