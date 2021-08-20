# -*- coding: UTF-8 -*-

# Copyright (c) 2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2021 Alberto Gacías <alberto@migasfree.org>
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

from ...utils import execute, get_setting

from .pms import Pms


class Pacman(Pms):
    """
    PMS for pacman based systems (Arch, Manjaro, KaOS, ...)
    """

    def __init__(self):
        super().__init__()

        self.name = 'pacman'
        self.relative_path = get_setting('MIGASFREE_REPOSITORY_TRAILING_PATH')
        self.mimetype = [
            'application/x-alpm-package',
            'application/x-zstd-compressed-alpm-package',
            'application/x-gtar',
        ]
        self.extensions = ['pkg', 'pkg.tar.zst', 'pkg.tar.gz', 'pkg.tar.xz']

    def create_repository(self, path, arch):
        """
        (int, string, string) create_repository(
            string path, string arch
        )
        FIXME
        """

        _cmd = '''
function create_deploy {
  cd %(path)s/%(components)s
  export GNUPGHOME=%(keys_path)s/.gnupg
  repo-add --sign --key migasfree-repository ./%(name)s.db.tar.gz ./*
}

create_deploy
''' % {
            'path': path,
            'name': os.path.basename(path),
            'keys_path': self.keys_path,
            'components': self.components
        }

        return execute(_cmd)

    def package_info(self, package):
        """
        string package_info(string package)
        """

        _cmd = '''
echo "## Info"
echo "~~~"
pacman --query --info --file %(pkg)s
echo "~~~"
echo
echo "## Changelog"
echo "~~~"
pacman --query --changelog --file %(pkg)s
echo "~~~"
echo
echo "## Files"
echo "~~~"
pacman --query --list --quiet --file %(pkg)s
echo "~~~"
        ''' % {'pkg': package}

        _ret, _output, _error = execute(_cmd)

        return _output if _ret == 0 else _error


    def package_metadata(self, package):
        """
        dict package_metadata(string package)
        """

        _cmd = 'pacman --query --info --file {}'.format(package)
        _ret, _output, _error = execute(_cmd)
        if _ret == 0:
            _output = _output.splitlines()
            _pkg_info = {}
            for _item in _output:
                if _item.startswith(('Name', 'Version', 'Architecture')):
                    key, value = _item.strip().split(':', 1)
                    _pkg_info[key.strip()] = value.strip()

            name = _pkg_info['Name']
            version = _pkg_info['Version']
            architecture = _pkg_info['Architecture']
        else:
            name, version, architecture = [None, None, None]

        return {
            'name': name,
            'version': version,
            'architecture': architecture
        }

    def source_template(self, deploy):
        """
        string source_template(Deployment deploy)
        FIXME SigLevel
        """

        from ..models import Deployment

        if deploy.source == Deployment.SOURCE_INTERNAL:
            return '[{name}]\nSigLevel = Optional TrustAll PackageTrustAll\n' \
                    'Server = {{protocol}}://{{server}}{media_url}{project}/{trailing_path}/{name}/{components}\n\n'.format(
                media_url=self.media_url,
                trailing_path=get_setting('MIGASFREE_REPOSITORY_TRAILING_PATH'),
                project=deploy.project.slug,
                name=deploy.slug,
                components=self.components
            )
        elif deploy.source == Deployment.SOURCE_EXTERNAL:
            return '[{name}]\nServer = {{protocol}}://{{server}}/src/{project}/{trailing_path}/{name}\n\n'.format(
                project=deploy.project.slug,
                trailing_path=get_setting('MIGASFREE_EXTERNAL_TRAILING_PATH'), 
                name=deploy.slug,
            )

        return ''
