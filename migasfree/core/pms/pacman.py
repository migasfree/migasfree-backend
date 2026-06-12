# Copyright (c) 2021-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2021-2026 Alberto Gacías <alberto@migasfree.org>
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
        self.architectures = ['any', 'x86_64']
        self.siglevel = 'Optional TrustAll PackageTrustAll'

    def create_repository(self, path, arch):
        """
        (int, string, string) create_repository(
            string path, string arch
        )
        """
        db_name = os.path.basename(path.rstrip('/'))
        component_dir = os.path.join(path, self.components)

        import glob

        files = []
        if os.path.isdir(component_dir):
            for ext in self.extensions:
                matched = glob.glob(os.path.join(component_dir, f'*.{ext}'))
                files.extend([os.path.basename(f) for f in matched])

        if not files:
            return 0, '', ''

        import os as python_os

        env = python_os.environ.copy()
        env['GNUPGHOME'] = os.path.join(self.keys_path, '.gnupg')

        cmd = ['repo-add', '--sign', '--key', 'migasfree-repository', f'./{db_name}.db.tar.gz', *files]

        return execute(cmd, shell=False, cwd=component_dir, env=env)

    def package_info(self, package):
        """
        string package_info(string package)
        """
        ret1, out1, err1 = execute([self.name, '--query', '--info', '--file', package], shell=False)
        if ret1 != 0:
            return err1 or out1

        _ret2, out2, _ = execute([self.name, '--query', '--changelog', '--file', package], shell=False)

        ret3, out3, err3 = execute([self.name, '--query', '--list', '--quiet', '--file', package], shell=False)
        if ret3 != 0:
            return err3 or out3

        output = f'## Info\n~~~\n{out1}~~~\n\n## Changelog\n~~~\n{out2}~~~\n\n## Files\n~~~\n{out3}~~~\n'
        return output

    def package_metadata(self, package):
        """
        dict package_metadata(string package)
        """

        cmd = [self.name, '--query', '--info', '--file', package]
        ret, output, _error = execute(cmd, shell=False)
        if ret == 0:
            output = output.splitlines()
            pkg_info = {}
            for item in output:
                if item.startswith(('Name', 'Version', 'Architecture')):
                    key, value = item.strip().split(':', 1)
                    pkg_info[key.strip()] = value.strip()

            name = pkg_info['Name']
            version = pkg_info['Version']
            architecture = pkg_info['Architecture']
        else:
            name, version, architecture = [None, None, None]

        return {'name': name, 'version': version, 'architecture': architecture}

    def source_template(self, deploy):
        """
        string source_template(Deployment deploy)
        """

        from ..models import Deployment

        if deploy.source == Deployment.SOURCE_INTERNAL:
            return """[{name}]
SigLevel = {siglevel}
Server = {{protocol}}://{{server}}{media_url}{project}/{trailing_path}/{name}/{components}

""".format(
                siglevel=self.siglevel,
                media_url=self.media_url,
                trailing_path=get_setting('MIGASFREE_REPOSITORY_TRAILING_PATH'),
                project=deploy.project.slug,
                name=deploy.slug,
                components=self.components,
            )
        elif deploy.source == Deployment.SOURCE_EXTERNAL:
            return '[{name}]\nServer = {{protocol}}://{{server}}/src/{project}/{trailing_path}/{name}\n\n'.format(
                project=deploy.project.slug,
                trailing_path=get_setting('MIGASFREE_EXTERNAL_TRAILING_PATH'),
                name=deploy.slug,
            )

        return ''
