# -*- coding: utf-8 -*-

# Copyright (c) 2015-2024 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2024 Alberto Gacías <alberto@migasfree.org>
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
Please, don't edit this file
Override or include settings at MIGASFREE_SETTINGS_OVERRIDE file
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MAX_FILE_SIZE = 1024 * 1024 * 50  # 50 MB

HOURLY_RANGE = 3  # days
DAILY_RANGE = 35  # days
MONTHLY_RANGE = 18  # months

MIGASFREE_FQDN = 'localhost'

MIGASFREE_STORE_TRAILING_PATH = 'stores'
MIGASFREE_REPOSITORY_TRAILING_PATH = 'repos'
MIGASFREE_EXTERNAL_TRAILING_PATH = 'external'
MIGASFREE_TMP_TRAILING_PATH = 'tmp'

MIGASFREE_AUTOREGISTER = True

MIGASFREE_COMPUTER_SEARCH_FIELDS = ('id', 'name')

MIGASFREE_SECONDS_MESSAGE_ALERT = 1800
MIGASFREE_ORGANIZATION = 'My Organization'
MIGASFREE_HELP_DESK = 'Put here how you want to be found'

MIGASFREE_SETTINGS_OVERRIDE = '/var/lib/migasfree-backend/conf/settings.py'
MIGASFREE_APP_DIR = BASE_DIR
MIGASFREE_PROJECT_DIR = os.path.dirname(MIGASFREE_APP_DIR)
MIGASFREE_TMP_DIR = '/tmp'
MIGASFREE_SECRET_DIR = os.path.join(BASE_DIR, 'secrets')

"""
MIGASFREE_EXTERNAL_ACTIONS
Sample:
     MIGASFREE_EXTERNAL_ACTIONS = {
        "computer": {
            "ping": {"title": "PING", "description": "check connectivity"},
            "ssh": {"title": "SSH", "description": "remote control via ssh"},
            "vnc": {"title": "VNC", "description": "remote control vnc", "many": False},
            "sync": {"title": "SYNC", "description": "ssh -> run migasfree -u"},
            "install": {
                "title": "INSTALL",
                "description": "ssh -> install a package",
                "related": ["deployment", "computer"]
            },
        },
        "error": {
            "clean": {"title": "delete", "description": "delete errors"},
        }
}
"""
MIGASFREE_EXTERNAL_ACTIONS = {}

MIGASFREE_INVALID_UUID = [
    '03000200-0400-0500-0006-000700080008',  # ASROCK
    '00000000-0000-0000-0000-000000000000',
    '00000000-0000-0000-0000-FFFFFFFFFFFF',
]

# Notifications
MIGASFREE_NOTIFY_NEW_COMPUTER = False
MIGASFREE_NOTIFY_CHANGE_UUID = False
MIGASFREE_NOTIFY_CHANGE_NAME = False
MIGASFREE_NOTIFY_CHANGE_IP = False

# PERIOD HARDWARE CAPTURE (DAYS)
MIGASFREE_HW_PERIOD = 30

# Programming Languages for Properties and Fault Definitions
MIGASFREE_PROGRAMMING_LANGUAGES = (
    (0, 'bash'),
    (1, 'python'),
    (2, 'perl'),
    (3, 'php'),
    (4, 'ruby'),
    (5, 'cmd'),
    (6, 'powershell'),
)

# Server Keys
MIGASFREE_PUBLIC_KEY = 'migasfree-server.pub'
MIGASFREE_PRIVATE_KEY = 'migasfree-server.pri'

# Packager Keys
MIGASFREE_PACKAGER_PUB_KEY = 'migasfree-packager.pub'
MIGASFREE_PACKAGER_PRI_KEY = 'migasfree-packager.pri'

# Default Computer Status
# Values: 'intended', 'reserved', 'unknown', 'in repair', 'available' or 'unsubscribed'
MIGASFREE_DEFAULT_COMPUTER_STATUS = 'intended'
