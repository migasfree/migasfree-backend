# -*- coding: UTF-8 -*-

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


class Pms:
    '''
    PMS: Package Management System
    Interface class
    Abstract methods
    '''

    @property
    def name(self):
        # Package Management System name
        raise NotImplementedError

    @property
    def relative_path(self):
        raise NotImplementedError

    @property
    def mimetype(self):
        raise NotImplementedError

    def __unicode__(self):
        '''
        string __unicode__(void)
        '''

        return self.name

    def create_repository(self, name, path, arch):
        '''
        (int, string, string) create_repository(
            string name, string path, string arch
        )
        '''

        raise NotImplementedError

    def package_info(self, package):
        '''
        string package_info(string package)
        '''

        raise NotImplementedError
