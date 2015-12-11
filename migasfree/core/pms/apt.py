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

from django.conf import settings

from .pms import Pms
from migasfree.utils import execute


class Apt(Pms):
    '''
    PMS for apt based systems (Debian, Ubuntu, Mint, ...)
    '''

    def __init__(self):
        self.name = 'apt'
        self.relative_path = 'repos/dists'
        self.mimetype = [
            'application/x-debian-package',
            'application/vnd.debian.binary-package',
        ]

    def create_repository(self, name, path, arch):
        '''
        (int, string, string) create_repository(
            string name, string path, string arch
        )
        '''

        _cmd = '''
_NAME=%(name)s
_ARCHS=("%(arch)s")
for _ARCH in ${_ARCHS[@]}
do
  cd %(path)s
  mkdir -p $_NAME/PKGS/binary-$_ARCH/
  cd ..

  dpkg-scanpackages -m dists/$_NAME/PKGS > dists/$_NAME/PKGS/binary-$_ARCH/Packages
  gzip -9c dists/$_NAME/PKGS/binary-$_ARCH/Packages > dists/$_NAME/PKGS/binary-$_ARCH/Packages.gz
done

function SUM {
  echo $1
  _FILES=$(find  -type f | sed 's/^.\///' | sort)
  for _FILE in $_FILES
    do
      _SIZE=$(printf "%%16d\\n" $(ls -l $_FILE | cut -d ' ' -f5))
      _MD5=$($2 $_FILE | cut -d ' ' -f1) $()
      echo " $_MD5" "$_SIZE" "$_FILE"
    done
}

function create_deploy {
  _F="/var/tmp/deploy"

  rm deploy 2>/dev/null || :
  rm deploy.gpg 2>/dev/null || :
  touch deploy
  rm $_F 2>/dev/null || :

  echo "Architectures: %(arch)s" > $_F
  echo "Codename: $_NAME" >> $_F
  echo "Components: PKGS" >> $_F
  echo "Date: $(date -u '+%%a, %%d %%b %%Y %%H:%%M:%%S UTC')" >> $_F
  echo "Label: migasfree  Repository" >> $_F
  echo "Origin: migasfree" >> $_F
  echo "Suite: $_NAME" >> $_F

  SUM "MD5Sum:" "md5sum" >> $_F
  SUM "SHA1:" "sha1sum" >> $_F
  SUM "SHA256:" "sha256sum" >> $_F
  SUM "SHA512:" "sha512sum" >> $_F

  mv $_F deploy

  gpg -u migasfree-repository --homedir %(keys_path)s/.gnupg --clearsign -o InRelease deploy
  gpg -u migasfree-repository --homedir %(keys_path)s/.gnupg -abs -o Release.gpg deploy
}

cd dists/$_NAME
create_deploy
''' % {
            'path': path,
            'name': name,
            'arch': arch,
            'keys_path': settings.MIGASFREE_KEYS_PATH
        }

        return execute(_cmd)

    def package_info(self, package):
        '''
        string package_info(string package)
        '''

        _cmd = '''
echo "****INFO****"
dpkg -I %(pkg)s
echo
echo
echo ****REQUIRES****
dpkg-deb --showformat='${Depends}' --show %(pkg)s
echo
echo
echo ****PROVIDES****
dpkg-deb --showformat='${Provides}' --show %(pkg)s
echo
echo
echo ****OBSOLETES****
dpkg-deb --showformat='${Replaces}' --show %(pkg)s
echo
echo
echo "****SCRIPT PREINST****"
dpkg-deb -I %(pkg)s preinst
echo
echo

echo "****SCRIPT POSTINST****"
dpkg-deb -I %(pkg)s postinst
echo
echo

echo "****SCRIPT PRERM****"
dpkg-deb -I %(pkg)s prerm
echo
echo

echo "****SCRIPT POSTRM****"
dpkg-deb -I %(pkg)s postrm
echo
echo

echo ****CHANGELOG****
_NAME=$(dpkg-deb --showformat='${Package}' --show %(pkg)s)
dpkg-deb --fsys-tarfile %(pkg)s | tar -O -xvf - ./usr/share/doc/$_NAME/changelog.Debian.gz | gunzip
echo
echo

echo ****FILES****
dpkg-deb -c %(pkg)s | awk '{print $6}'
        ''' % {'pkg': package}

        _ret, _output, _error = execute(_cmd)

        return _output if _ret == 0 else _error
