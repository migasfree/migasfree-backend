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
API v4 - Refactored into modules for better maintainability.
This package re-exports all functions for backward compatibility.
"""

# Helper functions
# Computer operations
from .computer import (
    get_computer,
    register_computer,
)

# Deprecated endpoints
from .deprecated import (
    upload_devices_changes,
)

# Faults and errors
from .faults import (
    upload_computer_errors,
    upload_computer_faults,
)
from .helpers import (
    add_notification_platform,
    add_notification_project,
    return_message,
    save_request_file,
)

# Inventory operations (software/hardware)
from .inventory import (
    get_computer_software,
    upload_computer_hardware,
    upload_computer_software_base,
    upload_computer_software_base_diff,
    upload_computer_software_history,
)

# Keys
from .keys import (
    get_key_packager,
)

# Packages and stores
from .packages import (
    get_package_data,
    upload_server_package,
    upload_server_set,
)

# Repositories
from .repositories import (
    create_repositories_of_packageset,
    create_repositories_package,
)

# Sync operations (core client-server communication)
from .sync import (
    get_properties,
    upload_computer_info,
    upload_computer_message,
)

# Tags
from .tags import (
    get_computer_tags,
    set_computer_tags,
)

__all__ = [  # noqa: RUF022
    # helpers
    'add_notification_platform',
    'add_notification_project',
    'return_message',
    'save_request_file',
    # computer
    'get_computer',
    'register_computer',
    # sync
    'get_properties',
    'upload_computer_info',
    'upload_computer_message',
    # inventory
    'upload_computer_hardware',
    'upload_computer_software_base',
    'upload_computer_software_base_diff',
    'upload_computer_software_history',
    'get_computer_software',
    # faults
    'upload_computer_errors',
    'upload_computer_faults',
    # tags
    'get_computer_tags',
    'set_computer_tags',
    # packages
    'get_package_data',
    'upload_server_package',
    'upload_server_set',
    # repositories
    'create_repositories_package',
    'create_repositories_of_packageset',
    # keys
    'get_key_packager',
    # deprecated
    'upload_devices_changes',
]
