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

    def create_repository(self, name, path):
        '''
        (int, string, string) create_repository(string name, string path)
        '''

        _cmd = '''
cd %(path)s
cd ..

DIST=%(name)s

ARCHS="i386 amd64 source"

mkdir .cache

mkdir -p dists/$DIST/PKGS/binary-amd64
mkdir -p dists/$DIST/PKGS/binary-i386
mkdir -p dists/$DIST/PKGS/source

    cat > apt-ftparchive.conf <<EOF
Dir {
    ArchiveDir ".";
    CacheDir "./.cache";
};

Default {
    Packages::Compress ". gzip bzip2";
    Contents::Compress ". gzip bzip2";
};

TreeDefault {
    BinCacheDB "packages-\$(SECTION)-\$(ARCH).db";
    Directory "dists/$DIST/\$(SECTION)";
    SrcDirectory "dists/$DIST/\$(SECTION)";
    Packages "\$(DIST)/\$(SECTION)/binary-\$(ARCH)/Packages";
    Contents "\$(DIST)/Contents-\$(ARCH)";
};

Tree "dists/$DIST" {
    Sections "PKGS";
    Architectures "$ARCHS";
}
EOF

apt-ftparchive generate apt-ftparchive.conf 2> ./err
if [ $? != 0 ]
then
    cat ./err >&2
fi
rm ./err

cat > apt-release.conf <<EOF
APT::FTPArchive::Release::Codename "$DIST";
APT::FTPArchive::Release::Origin "migasfree";
APT::FTPArchive::Release::Components "PKGS";
APT::FTPArchive::Release::Label "migasfree $DISTRO Repository";
APT::FTPArchive::Release::Architectures "$ARCHS";
APT::FTPArchive::Release::Suite "$DIST";
EOF

apt-ftparchive -c apt-release.conf release dists/$DIST > dists/$DIST/Release
gpg -u migasfree-repository --homedir %(keys_path)s/.gnupg -abs -o dists/$DIST/Release.gpg dists/$DIST/Release
rm -rf apt-release.conf apt-ftparchive.conf
        ''' % {
            'path': path,
            'name': name,
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
