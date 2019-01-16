# -*- coding: UTF-8 -*-

# Copyright (c) 2015-2019 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2019 Alberto Gacías <alberto@migasfree.org>
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

import os

from django.conf import settings

from .pms import Pms
from migasfree.utils import execute


class Yum(Pms):
    """
    PMS for yum based systems (Fedora, Red Hat, CentOS, ...)
    """

    def __init__(self):
        self.name = 'yum'
        self.relative_path = 'repos'
        self.mimetype = [
            'application/x-rpm',
            'application/x-redhat-package-manager'
        ]

    def create_repository(self, path, arch):
        """
        (int, string, string) create_repository(
            string path, string arch
        )
        """

        _cmd = '''
_DIR=%(path)s/%(name)s
rm -rf $_DIR/repodata
rm -rf $_DIR/checksum
createrepo --cachedir checksum $_DIR
gpg -u migasfree-repository --homedir %(keys_path)s/.gnupg --detach-sign --armor $_DIR/repodata/repomd.xml
        ''' % {
            'path': path,
            'name': os.path.basename(path),
            'keys_path': settings.MIGASFREE_KEYS_DIR
        }

        return execute(_cmd)

    def package_info(self, package):
        """
        string package_info(string package)
        """

        _cmd = '''
echo ****INFO****
rpm -qp --info %(pkg)s
echo
echo
echo ****REQUIRES****
rpm -qp --requires %(pkg)s
echo
echo
echo ****PROVIDES****
rpm -qp --provides %(pkg)s
echo
echo
echo ****OBSOLETES****
rpm -qp --obsoletes %(pkg)s
echo
echo
echo ****SCRIPTS****
rpm -qp --scripts %(pkg)s
echo
echo
echo ****CHANGELOG****
rpm -qp --changelog %(pkg)s
echo
echo
echo ****FILES****
rpm -qp --list %(pkg)s
echo
        ''' % {'pkg': package}

        _ret, _output, _error = execute(_cmd)

        return _output if _ret == 0 else _error
