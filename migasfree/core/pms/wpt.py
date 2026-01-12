# Copyright (c) 2024-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2024-2026 Alberto Gacías <alberto@migasfree.org>
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

import hashlib
import json
import os
import tarfile

from ...utils import get_setting
from .pms import Pms


class Wpt(Pms):
    """
    PMS for Windows Package Tool (Microsoft Windows)
    """

    def __init__(self):
        super().__init__()

        self.name = 'wpt'
        self.relative_path = get_setting('MIGASFREE_REPOSITORY_TRAILING_PATH')
        self.mimetype = ['application/gzip', 'application/x-gzip']
        self.extensions = ['tar.gz']
        self.architectures = ['x64']

    def create_repository(self, path, arch):
        """
        (int, string, string) create_repository(
            string path, string arch
        )
        """

        repository_info = {}

        for package_file in os.listdir(os.path.join(path, self.components)):
            package_path = os.path.join(path, self.components, package_file)

            if os.path.isfile(package_path) and tarfile.is_tarfile(package_path):
                with open(package_path, 'rb') as f:
                    hash_ = hashlib.sha256(f.read()).hexdigest()

                metadata = self.package_metadata(package_path)

                if metadata['name'] not in repository_info:
                    repository_info[metadata['name']] = {}

                repository_info[metadata['name']][metadata['version']] = {
                    'metadata': metadata,
                    'filename': f'{self.components}/{package_file}',
                    'hash': hash_,
                }

        packages_file = os.path.join(path, 'packages.json')
        with open(packages_file, 'w') as f:
            json.dump(repository_info, f, indent=2)

        return 0, repository_info, ''

    def package_info(self, package):
        """
        string package_info(string package)
        """

        temp_path = get_setting('MIGASFREE_TMP_DIR')
        output = ''

        with tarfile.open(package, 'r:gz') as tar:
            if 'pms/metadata.json' in tar.getnames():
                tar.extract('pms/metadata.json', path=temp_path)

                with open(f'{temp_path}/pms/metadata.json') as f:
                    metadata = json.load(f)

                output += '## Info (pms/metadata.json)\n'
                output += '~~~\n'
                output += f'Name: {metadata["name"]}\n'
                output += f'Version: {metadata["version"]}\n'
                output += f'Description: {metadata["description"]}\n'
                output += f'Maintainer: {metadata["maintainer"]}\n'
                output += f'Specification: {metadata["specification"]}\n'
                if 'homepage' in metadata:
                    output += f'Homepage: {metadata["homepage"]}\n'
                if 'dependencies' in metadata:
                    output += f'Dependencies: {metadata["dependencies"]}\n'
                output += '~~~\n'

            if 'pms/readme.md' in tar.getnames():
                tar.extract('pms/readme.md', path=temp_path)

                with open(f'{temp_path}/pms/readme.md') as f:
                    readme_contents = f.read()

                output += '## Readme (pms/readme.md)\n'
                output += '~~~\n'
                output += f'{readme_contents}\n'
                output += '~~~\n'

            if 'pms/changelog.md' in tar.getnames():
                tar.extract('pms/changelog.md', path=temp_path)

                with open(f'{temp_path}/pms/changelog.md') as f:
                    changelog_contents = f.read()

                output += '## Readme (pms/changelog.md)\n'
                output += '~~~\n'
                output += f'{changelog_contents}\n'
                output += '~~~\n'

            script_names = ['preinst', 'install', 'postinst', 'prerm', 'remove', 'postrm']
            script_extensions = ['.ps1', '.cmd', '.py']

            for script_name in script_names:
                for script_extension in script_extensions:
                    script_path = f'pms/{script_name}{script_extension}'

                    if script_path in tar.getnames():
                        tar.extract(script_path, path=temp_path)

                        with open(f'{temp_path}/{script_path}') as f:
                            script_contents = f.read()

                        output += f'## Script {script_path}\n'
                        output += '~~~\n'
                        output += f'{script_contents}\n'
                        output += '~~~\n'

            if 'data/' in tar.getnames():
                print('Contents of data directory:')
                output += '## Files\n'
                output += '~~~\n'
                for member in tar.getmembers():
                    if member.name.startswith('data/'):
                        print(member.name)
                        output += f'{member.name}\n'

                output += '~~~\n'

        return output

    def package_metadata(self, package):
        """
        dict package_metadata(string package)
        """

        temp_path = get_setting('MIGASFREE_TMP_DIR')

        with tarfile.open(package, 'r:gz') as tar:
            metadata_file = tar.getmember('pms/metadata.json')
            tar.extract(metadata_file, path=temp_path)

        with open(f'{temp_path}/pms/metadata.json') as f:
            metadata = json.load(f)

        metadata['architecture'] = 'x64'

        return metadata

    def source_template(self, deploy):
        """
        string source_template(Deployment deploy)
        """

        from ..models import Deployment

        if deploy.source == Deployment.SOURCE_INTERNAL:
            return '{{protocol}}://{{server}}{media_url}{project}/{trailing_path}/{name} {components}\n'.format(
                media_url=self.media_url,
                project=deploy.project.slug,
                trailing_path=get_setting('MIGASFREE_REPOSITORY_TRAILING_PATH'),
                name=deploy.slug,
                components=self.components,
            )

        if deploy.source == Deployment.SOURCE_EXTERNAL:
            return '{{protocol}}://{{server}}/src/{project}/{trailing_path}/{name} {suite} {components}\n'.format(
                project=deploy.project.slug,
                trailing_path=get_setting('MIGASFREE_EXTERNAL_TRAILING_PATH'),
                name=deploy.slug,
                suite=deploy.suite,
                components=deploy.components,
            )

        return ''
