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

import gzip
import hashlib
import os
import re
import subprocess
from datetime import UTC, datetime

from ...utils import execute, get_setting
from .pms import Pms


class Apt(Pms):
    """
    PMS for apt based systems (Debian, Ubuntu, Mint, ...)
    """

    def __init__(self):
        super().__init__()

        self.name = 'apt'
        self.relative_path = os.path.join(get_setting('MIGASFREE_REPOSITORY_TRAILING_PATH'), 'dists')
        self.mimetype = [
            'application/x-debian-package',
            'application/vnd.debian.binary-package',
        ]
        self.extensions = ['deb']
        self.architectures = [
            'alpha',
            'all',
            'amd64',
            'arm',
            'arm64',
            'armel',
            'armhf',
            'avr32',
            'hppa',
            'hurd-i386',
            'i386',
            'ia64',
            'kfreebsd-amd64',
            'kfreebsd-i386',
            'loong64',
            'm68k',
            'mips',
            'mips64el',
            'mipsel',
            'powerpc',
            'powerpcspe',
            'ppc64',
            'ppc64el',
            'riscv64',
            's390',
            's390x',
            'sh4',
            'sparc',
            'sparc64',
            'x32',
        ]

    def create_repository(self, path, arch):
        """
        (int, string, string) create_repository(
            string path, string arch
        )
        """

        repo_name = os.path.basename(path)
        cwd = os.path.abspath(os.path.join(path, '..', '..'))

        def calculate_hash(base_dir, hash_algo):
            files = []
            for root, _, filenames in os.walk(base_dir):
                for filename in filenames:
                    if filename.startswith('Release'):
                        continue
                    abs_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(abs_path, base_dir)
                    files.append((rel_path, abs_path))

            files.sort(key=lambda x: x[0])

            lines = []
            for rel_path, abs_path in files:
                h = hashlib.new(hash_algo)
                try:
                    size = os.path.getsize(abs_path)
                    with open(abs_path, 'rb') as f:
                        for chunk in iter(lambda: f.read(65536), b''):
                            h.update(chunk)
                    digest = h.hexdigest()
                    lines.append(f' {digest} {size:16d} {rel_path}')
                except OSError:
                    pass
            return lines

        for arch_name in arch.split():
            binary_dir = os.path.join(path, self.components, f'binary-{arch_name}')
            os.makedirs(binary_dir, exist_ok=True)

            cmd = [
                'ionice',
                '-c',
                '3',
                'apt-ftparchive',
                '--arch',
                arch_name,
                'packages',
                f'dists/{repo_name}/{self.components}',
            ]
            ret, out, err = execute(cmd, shell=False, cwd=cwd)
            if ret != 0:
                return ret, out, err

            store_trailing_path = get_setting('MIGASFREE_STORE_TRAILING_PATH')
            out = re.sub(
                r'Filename: .*/' + re.escape(self.components) + r'/',
                f'Filename: dists/{repo_name}/{self.components}/',
                out,
            )
            out = re.sub(
                r'Filename: .*/' + re.escape(store_trailing_path) + r'/[^/]*/',
                f'Filename: dists/{repo_name}/{self.components}/',
                out,
            )

            packages_file = os.path.join(binary_dir, 'Packages')
            with open(packages_file, 'w', encoding='utf-8') as f:
                f.write(out)

            with open(packages_file, 'rb') as f_in, gzip.open(packages_file + '.gz', 'wb', compresslevel=9) as f_out:
                f_out.writelines(f_in)

        release_path = os.path.join(path, 'Release')
        md5_lines = calculate_hash(path, 'md5')
        sha1_lines = calculate_hash(path, 'sha1')
        sha256_lines = calculate_hash(path, 'sha256')
        sha512_lines = calculate_hash(path, 'sha512')

        date_str = datetime.now(UTC).strftime('%a, %d %b %Y %H:%M:%S UTC')

        release_content = (
            f'Architectures: {arch}\n'
            f'Codename: {repo_name}\n'
            f'Components: {self.components}\n'
            f'Date: {date_str}\n'
            f'Label: migasfree {repo_name} repository\n'
            f'Origin: migasfree\n'
            f'Suite: {repo_name}\n'
            'MD5Sum:\n'
            + ('\n'.join(md5_lines) + '\n' if md5_lines else '')
            + 'SHA1:\n'
            + ('\n'.join(sha1_lines) + '\n' if sha1_lines else '')
            + 'SHA256:\n'
            + ('\n'.join(sha256_lines) + '\n' if sha256_lines else '')
            + 'SHA512:\n'
            + ('\n'.join(sha512_lines) + '\n' if sha512_lines else '')
        )

        with open(release_path, 'w', encoding='utf-8') as f:
            f.write(release_content)
        os.chmod(release_path, 0o644)

        gpg_homedir = os.path.join(self.keys_path, '.gnupg')
        ret_in, out_in, err_in = execute(
            [
                'gpg',
                '--batch',
                '--no-tty',
                '--local-user',
                'migasfree-repository',
                '--homedir',
                gpg_homedir,
                '--clear-sign',
                '--output',
                'InRelease',
                'Release',
            ],
            shell=False,
            cwd=path,
        )
        if ret_in != 0:
            return ret_in, out_in, err_in

        ret_gpg, out_gpg, err_gpg = execute(
            [
                'gpg',
                '--batch',
                '--no-tty',
                '--local-user',
                'migasfree-repository',
                '--homedir',
                gpg_homedir,
                '-abs',
                '--output',
                'Release.gpg',
                'Release',
            ],
            shell=False,
            cwd=path,
        )
        if ret_gpg != 0:
            return ret_gpg, out_gpg, err_gpg

        return 0, '', ''

    def package_info(self, package):
        """
        string package_info(string package)
        """

        def get_changelog(pkg_path, pkg_name):
            for path_in_tar in [
                f'./usr/share/doc/{pkg_name}/changelog.Debian.gz',
                f'./usr/share/doc/{pkg_name}/changelog.gz',
            ]:
                try:
                    p1 = subprocess.Popen(['dpkg-deb', '--fsys-tarfile', pkg_path], stdout=subprocess.PIPE)
                    p2 = subprocess.Popen(
                        ['tar', '-O', '-xf', '-', path_in_tar],
                        stdin=p1.stdout,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                    )
                    p1.stdout.close()
                    out_bytes, _ = p2.communicate()
                    if p2.returncode == 0 and out_bytes:
                        return gzip.decompress(out_bytes).decode('utf-8', errors='replace')
                except Exception:
                    pass
            return '[Changelog not found or empty]'

        ret1, out_info, err_info = execute(['dpkg-deb', '--info', package], shell=False)
        if ret1 != 0:
            return err_info or out_info

        format_str = (
            '## Requires\n~~~\n${Depends}\n~~~\n\n'
            '## Provides\n~~~\n${Provides}\n~~~\n\n'
            '## Obsoletes\n~~~\n${Replaces}\n~~~\n\n'
            '${Package}'
        )
        ret2, out_show, err_show = execute(['dpkg-deb', f'--showformat={format_str}', '--show', package], shell=False)
        if ret2 != 0:
            return err_show or out_show

        lines_show = out_show.splitlines()
        pkg_name = lines_show[-1].strip() if lines_show else ''
        deps_show = '\n'.join(lines_show[:-1]) if lines_show else ''

        scripts = {}
        for script_name in ['preinst', 'postinst', 'prerm', 'postrm']:
            ret_s, out_s, _ = execute(['dpkg-deb', '--info', package, script_name], shell=False)
            scripts[script_name] = out_s if ret_s == 0 else '[None]'

        changelog = get_changelog(package, pkg_name)

        ret_files, out_files, _ = execute(['dpkg-deb', '-c', package], shell=False)
        file_list = []
        if ret_files == 0:
            for line in out_files.splitlines():
                parts = line.strip().split(None, 5)
                if len(parts) >= 6:
                    file_list.append(parts[5])
        files_str = '\n'.join(file_list)

        output = (
            '## Info\n'
            '~~~\n'
            f'{out_info}'
            '~~~\n\n'
            f'{deps_show}\n\n'
            '## Script PreInst\n'
            '~~~\n'
            f'{scripts["preinst"]}\n'
            '~~~\n\n'
            '## Script PostInst\n'
            '~~~\n'
            f'{scripts["postinst"]}\n'
            '~~~\n\n'
            '## Script PreRm\n'
            '~~~\n'
            f'{scripts["prerm"]}\n'
            '~~~\n\n'
            '## Script PostRm\n'
            '~~~\n'
            f'{scripts["postrm"]}\n'
            '~~~\n\n'
            '## Changelog\n'
            '~~~\n'
            f'{changelog}\n'
            '~~~\n\n'
            '## Files\n'
            '~~~\n'
            f'{files_str}\n'
            '~~~\n'
        )
        return output

    def package_metadata(self, package):
        """
        dict package_metadata(string package)
        """

        cmd = ['dpkg-deb', '--showformat=${Package}_${Version}_${Architecture}', '--show', package]
        ret, output, _ = execute(cmd, shell=False)

        if ret == 0:
            name, version, architecture = output.split('_')
        else:
            name, version, architecture = None, None, None

        return {'name': name, 'version': version, 'architecture': architecture}

    def source_template(self, deploy):
        """
        string source_template(Deployment deploy)
        """

        from ..models import Deployment

        if deploy.source == Deployment.SOURCE_INTERNAL:
            return 'deb {{protocol}}://{{server}}{media_url}{project}/{trailing_path} {name} {components}\n'.format(
                media_url=self.media_url,
                project=deploy.project.slug,
                trailing_path=get_setting('MIGASFREE_REPOSITORY_TRAILING_PATH'),
                name=deploy.slug,
                components=self.components,
            )
        elif deploy.source == Deployment.SOURCE_EXTERNAL:
            return (
                'deb {options} {{protocol}}://{{server}}/src/{project}/{trailing_path}/{name} '
                '{suite} {components}\n'.format(
                    options=deploy.options if deploy.options else '',
                    project=deploy.project.slug,
                    trailing_path=get_setting('MIGASFREE_EXTERNAL_TRAILING_PATH'),
                    name=deploy.slug,
                    suite=deploy.suite,
                    components=deploy.components,
                )
            )

        return ''
