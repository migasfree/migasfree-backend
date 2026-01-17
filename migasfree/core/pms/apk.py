# Copyright (c) 2025-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2025-2026 Alberto Gacías <alberto@migasfree.org>
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


class Apk(Pms):
    """
    PMS for Alpine systems (Alpine Package Keeper)
    """

    def __init__(self):
        super().__init__()

        self.name = 'apk'
        self.relative_path = os.path.join(get_setting('MIGASFREE_REPOSITORY_TRAILING_PATH'), 'dists')
        self.mimetype = [
            'application/x-alpine-package',
            'application/vnd.alpine.package',
        ]
        self.extensions = ['apk']
        self.architectures = [
            'aarch64',
            'armhf',
            'armv7',
            'loongarch64',
            'mips64',
            'ppc64le',
            'riscv64',
            's390x',
            'x86',
            'x86_64',
        ]

    def create_repository(self, path, arch):
        """
        (int, string, string) create_repository(
            string path, string arch
        )
        """

        name = os.path.basename(path)
        cmd = rf"""
_NAME={name}
_ARCHS=("{arch}")
for _ARCH in ${{_ARCHS[@]}}
do
  mkdir -p "{path}/{self.components}/$_ARCH/"
  cd {path}/../..

  apk index -o dists/$_NAME/{self.components}/$_ARCH/APKINDEX.tar.gz \
    dists/$_NAME/{self.components}/*.apk

  if [ -f "{self.keys_path}/migasfree.rsa" ]; then
    abuild-sign -k "{self.keys_path}/migasfree.rsa" \
      dists/$_NAME/{self.components}/$_ARCH/APKINDEX.tar.gz
  fi
done
"""

        return execute(cmd, shell=True)

    def package_info(self, package):
        """
        string package_info(string package)
        """

        cmd = rf"""
echo "## Info"
echo "~~~"
tar -zxf {package} .PKGINFO -O
echo "~~~"
echo
echo "## Files"
echo "~~~"
tar -tf {package} | grep -v '^\.PKGINFO$' | grep -v '^\.SIGN\.'
echo "~~~"
        """

        ret, output, error = execute(cmd, shell=True)

        return output if ret == 0 else error

    def package_metadata(self, package):
        """
        dict package_metadata(string package)
        """

        cmd = f'tar -zxf {package} .PKGINFO -O'
        ret, output, _error = execute(cmd, shell=True)

        name, version, architecture = None, None, None

        if ret == 0:
            for line in output.splitlines():
                if line.startswith('pkgname = '):
                    name = line.split(' = ')[1].strip()
                elif line.startswith('pkgver = '):
                    version = line.split(' = ')[1].strip()
                elif line.startswith('arch = '):
                    architecture = line.split(' = ')[1].strip()

        return {'name': name, 'version': version, 'architecture': architecture}

    def source_template(self, deploy):
        """
        string source_template(Deployment deploy)
        """

        from ..models import Deployment

        if deploy.source == Deployment.SOURCE_INTERNAL:
            return '{{protocol}}://{{server}}{media_url}{project}/{trailing_path}/{name}/{components}\n'.format(
                media_url=self.media_url,
                project=deploy.project.slug,
                trailing_path=get_setting('MIGASFREE_REPOSITORY_TRAILING_PATH'),
                name=deploy.slug,
                components=self.components,
            )
        elif deploy.source == Deployment.SOURCE_EXTERNAL:
            return '{{protocol}}://{{server}}/src/{project}/{trailing_path}/{name}/{components}\n'.format(
                project=deploy.project.slug,
                trailing_path=get_setting('MIGASFREE_EXTERNAL_TRAILING_PATH'),
                name=deploy.slug,
                components=deploy.components,
            )

        return ''
