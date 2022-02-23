# -*- coding: UTF-8 -*-

# Copyright (c) 2015-2022 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2022 Alberto Gacías <alberto@migasfree.org>
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

from ...utils import get_setting


class Pms:
    """
    PMS: Package Management System
    Interface class
    Abstract methods
    """

    name = ''  # Package Management System name
    relative_path = ''
    mimetype = []
    components = 'PKGS'
    extensions = []

    def __init__(self):
        self.keys_path = get_setting('MIGASFREE_KEYS_DIR')
        self.media_url = get_setting('MEDIA_URL')

    def __str__(self):
        """
        string __str__(void)
        """

        return self.name

    def create_repository(self, path, arch):
        """
        (int, string, string) create_repository(
            string path, string arch
        )
        """

        raise NotImplementedError

    def package_info(self, package):
        """
        string package_info(string package)
        """

        raise NotImplementedError


    def package_metadata(self, package):
        """
        dict package_metadata(string package)
        """

        raise NotImplementedError

    def source_template(self, deploy):
        """
        string source_template(Deployment deploy)
        """

        raise NotImplementedError
