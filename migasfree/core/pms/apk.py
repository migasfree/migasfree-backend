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
        import glob

        repo_name = os.path.basename(path)
        cwd = os.path.abspath(os.path.join(path, '..', '..'))

        for arch_name in arch.split():
            binary_dir = os.path.join(path, self.components, arch_name)
            os.makedirs(binary_dir, exist_ok=True)

            apk_pattern = f'dists/{repo_name}/{self.components}/*.apk'
            apk_files = glob.glob(os.path.join(cwd, apk_pattern))
            apk_files_rel = [os.path.relpath(f, cwd) for f in apk_files]

            output_index = f'dists/{repo_name}/{self.components}/{arch_name}/APKINDEX.tar.gz'
            cmd_index = ['apk', 'index', '-o', output_index, *apk_files_rel]
            ret_idx, out_idx, err_idx = execute(cmd_index, shell=False, cwd=cwd)
            if ret_idx != 0:
                return ret_idx, out_idx, err_idx

            rsa_key = os.path.join(self.keys_path, 'migasfree.rsa')
            if os.path.isfile(rsa_key):
                cmd_sign = ['abuild-sign', '-k', rsa_key, output_index]
                ret_sign, out_sign, err_sign = execute(cmd_sign, shell=False, cwd=cwd)
                if ret_sign != 0:
                    return ret_sign, out_sign, err_sign

        return 0, '', ''

    def package_info(self, package):
        """
        string package_info(string package)
        """
        ret1, out_info, err_info = execute(['tar', '-zxf', package, '.PKGINFO', '-O'], shell=False)
        if ret1 != 0:
            return err_info or out_info

        ret2, out_files, err_files = execute(['tar', '-tf', package], shell=False)
        if ret2 != 0:
            return err_files or out_files

        filtered_files = []
        for line in out_files.splitlines():
            line = line.strip()
            if line == '.PKGINFO' or line.startswith('.SIGN.'):
                continue
            filtered_files.append(line)

        files_str = '\n'.join(filtered_files)

        output = f'## Info\n~~~\n{out_info}~~~\n\n## Files\n~~~\n{files_str}\n~~~\n'
        return output

    def package_metadata(self, package):
        """
        dict package_metadata(string package)
        """

        cmd = ['tar', '-zxf', package, '.PKGINFO', '-O']
        ret, output, _error = execute(cmd, shell=False)

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
