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

import os
import shlex

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

        cmd = r"""
set -e
_NAME={name}
_ARCHS=("{arch}")
for _ARCH in ${{_ARCHS[@]}}
do
  mkdir -p "{path}/{components}/binary-$_ARCH/"
  cd {path}/../..

  ionice -c 3 apt-ftparchive --arch $_ARCH packages dists/$_NAME/{components} \
    > dists/$_NAME/{components}/binary-$_ARCH/Packages 2> /tmp/$_NAME

  sed -i "s/Filename: .*\/{components}\//Filename: dists\/$_NAME\/{components}\//" \
    dists/$_NAME/{components}/binary-$_ARCH/Packages
  sed -i "s/Filename: .*\/{store_trailing_path}\/[^/]*\//Filename: \
    dists\/$_NAME\/{components}\//" dists/$_NAME/{components}/binary-$_ARCH/Packages
  gzip -9c dists/$_NAME/{components}/binary-$_ARCH/Packages > dists/$_NAME/{components}/binary-$_ARCH/Packages.gz
done

function calculate_hash {{
  echo "$1"
  find . -type f ! -name "Release*" | sed 's/^.\///' | sort | while read -r _FILE
  do
    _SIZE=$(printf "%16d" $(stat -c "%s" "$_FILE"))
    _HASH=$($2 "$_FILE" | cut -d ' ' -f1)
    echo " $_HASH $_SIZE $_FILE"
  done
}}

function create_deploy {{
  cd {path}
  _F="$(mktemp /var/tmp/deploy-XXXXX)"

  echo "Architectures: ${{_ARCHS[@]}}" > "$_F"
  echo "Codename: $_NAME" >> "$_F"
  echo "Components: {components}" >> "$_F"
  echo "Date: $(LC_ALL=C date -u '+%a, %d %b %Y %H:%M:%S UTC')" >> "$_F"
  echo "Label: migasfree $_NAME repository" >> "$_F"
  echo "Origin: migasfree" >> "$_F"
  echo "Suite: $_NAME" >> "$_F"

  calculate_hash "MD5Sum:" "md5sum" >> "$_F"
  calculate_hash "SHA1:" "sha1sum" >> "$_F"
  calculate_hash "SHA256:" "sha256sum" >> "$_F"
  calculate_hash "SHA512:" "sha512sum" >> "$_F"

  mv "$_F" Release
  chmod 644 Release

  gpg --batch --no-tty --local-user migasfree-repository --homedir {keys_path}/.gnupg --clear-sign --output InRelease Release
  gpg --batch --no-tty --local-user migasfree-repository --homedir {keys_path}/.gnupg -abs --output Release.gpg Release
}}

create_deploy
""".format(
            path=shlex.quote(path),
            name=shlex.quote(os.path.basename(path)),
            arch=shlex.quote(arch),
            keys_path=shlex.quote(self.keys_path),
            components=shlex.quote(self.components),
            store_trailing_path=shlex.quote(get_setting('MIGASFREE_STORE_TRAILING_PATH')),
        )

        return execute(cmd, shell=True)

    def package_info(self, package):
        """
        string package_info(string package)
        """

        package_safe = shlex.quote(package)

        # Optimized field extraction using a single dpkg-deb --show call
        format_str = (
            '## Requires\\n~~~\\n${Depends}\\n~~~\\n\\n'
            '## Provides\\n~~~\\n${Provides}\\n~~~\\n\\n'
            '## Obsoletes\\n~~~\\n${Replaces}\\n~~~\\n\\n'
            '## PackageName\\n${Package}'
        )

        cmd = f"""
set -e
echo "## Info"
echo "~~~"
dpkg-deb --info {package_safe}
echo "~~~"
echo

# Multi-field extraction
_OUT=$(dpkg-deb --showformat='{format_str}' --show {package_safe})
_NAME=$(echo "$_OUT" | tail -n 1)
echo "$_OUT" | head -n -2

echo "## Script PreInst"
echo "~~~"
dpkg-deb --info {package_safe} preinst 2>/dev/null || echo "[None]"
echo "~~~"
echo
echo "## Script PostInst"
echo "~~~"
dpkg-deb --info {package_safe} postinst 2>/dev/null || echo "[None]"
echo "~~~"
echo
echo "## Script PreRm"
echo "~~~"
dpkg-deb --info {package_safe} prerm 2>/dev/null || echo "[None]"
echo "~~~"
echo
echo "## Script PostRm"
echo "~~~"
dpkg-deb --info {package_safe} postrm 2>/dev/null || echo "[None]"
echo "~~~"
echo
echo "## Changelog"
echo "~~~"
# Try to extract changelog more efficiently
dpkg-deb --fsys-tarfile {package_safe} | tar -O -xf - ./usr/share/doc/$_NAME/changelog.Debian.gz 2>/dev/null | gunzip 2>/dev/null || \\
dpkg-deb --fsys-tarfile {package_safe} | tar -O -xf - ./usr/share/doc/$_NAME/changelog.gz 2>/dev/null | gunzip 2>/dev/null || \\
echo "[Changelog not found or empty]"
echo "~~~"
echo
echo "## Files"
echo "~~~"
dpkg-deb -c {package_safe} | awk '{{{{print $6}}}}'
echo "~~~"
"""

        ret, output, error = execute(cmd, shell=True)

        return output if ret == 0 else error

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
