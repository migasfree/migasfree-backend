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
Safe views package - JWT-authenticated endpoints for computer synchronization.

This package contains:
- helpers: Utility functions for computer/user management
- transmission: EOT and Synchronization views
- computer: SafeComputerViewSet with all computer-related actions
"""

from .computer import SafeComputerViewSet
from .helpers import get_computer, get_user_or_create, is_computer_changed
from .transmission import SafeEndOfTransmissionView, SafeSynchronizationView

__all__ = [
    'SafeComputerViewSet',
    'SafeEndOfTransmissionView',
    'SafeSynchronizationView',
    'get_computer',
    'get_user_or_create',
    'is_computer_changed',
]
