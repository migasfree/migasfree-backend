# -*- coding: UTF-8 -*-

# Copyright (c) 2015-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2021 Alberto Gacías <alberto@migasfree.org>
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


class Yum(Pms):
    """
    PMS for yum based systems (Fedora, Red Hat, CentOS, ...)
    """

    def __init__(self):
        super().__init__()

        self.name = 'yum'
        self.relative_path = get_setting('MIGASFREE_REPOSITORY_TRAILING_PATH')
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
_DIR=%(path)s
rm -rf $_DIR/repodata
rm -rf $_DIR/checksum
createrepo --cachedir checksum $_DIR
gpg -u migasfree-repository --homedir %(keys_path)s/.gnupg --detach-sign --armor $_DIR/repodata/repomd.xml
        ''' % {
            'path': path,
            'keys_path': self.keys_path
        }

        return execute(_cmd)

    def package_info(self, package):
        """
        string package_info(string package)
        """

        _cmd = '''
echo "## Info"
echo "~~~"
rpm -qp --info %(pkg)s
echo "~~~"
echo
echo "## Requires"
echo "~~~"
rpm -qp --requires %(pkg)s
echo "~~~"
echo
echo "## Provides"
echo "~~~"
rpm -qp --provides %(pkg)s
echo "~~~"
echo
echo "## Obsoletes"
echo "~~~"
rpm -qp --obsoletes %(pkg)s
echo "~~~"
echo
echo "## Scripts"
echo "~~~"
rpm -qp --scripts %(pkg)s
echo "~~~"
echo
echo "## Changelog"
echo "~~~"
rpm -qp --changelog %(pkg)s
echo "~~~"
echo
echo "## Files"
echo "~~~"
rpm -qp --list %(pkg)s
echo "~~~"
        ''' % {'pkg': package}

        _ret, _output, _error = execute(_cmd)

        return _output if _ret == 0 else _error

    def package_metadata(self, package):
        """
        dict package_metadata(string package)
        """

        _cmd = 'rpm -qp --queryformat "%%{NAME}___%%{VERSION}-%%{RELEASE}___%%{ARCH}" %s 2>/dev/null' % package
        _ret, _output, _error = execute(_cmd)
        if _ret == 0:
            name, version, architecture = _output.split('___', 2)
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
        """

        from ..models import Deployment

        if deploy.source == Deployment.SOURCE_INTERNAL:
            return """[REPO-{name}]
name=REPO-{name}
baseurl={{protocol}}://{{server}}{media_url}{project}/{trailing_path}/{name}
enabled=1
http_caching=none
repo_gpgcheck=1
gpgcheck=0
gpgkey=file://{{keys_path}}/{{server}}/repositories.pub
""".format(
                media_url=self.media_url,
                project=deploy.project.slug,
                trailing_path=get_setting('MIGASFREE_REPOSITORY_TRAILING_PATH'),
                name=deploy.slug
            )
        elif deploy.source == Deployment.SOURCE_EXTERNAL:
            normal_template = """[EXTERNAL-{name}]
name=EXTERNAL-{name}
baseurl={{protocol}}://{{server}}/src/{project}/{trailing_path}/{name}/{suite}/$basearch/
{options}
"""
            components_template = """[EXTERNAL-{name}]
name=EXTERNAL-{name}
baseurl={{protocol}}://{{server}}/src/{project}/{trailing_path}/{name}/{suite}/{component}
{options}
"""
            if deploy.components:
                template = ''
                for component in deploy.components.split(' '):
                    template += components_template.format(
                        project=deploy.project.slug,
                        name='{}-{}'.format(deploy.slug, component.replace('/', '-')),
                        trailing_path=get_setting('MIGASFREE_EXTERNAL_TRAILING_PATH'),
                        suite=deploy.suite,
                        options=deploy.options.replace(' ', '\n') if deploy.options else '',
                        component=component
                    )

                return template
            else:
                return normal_template.format(
                    project=deploy.project.slug,
                    name=deploy.slug,
                    trailing_path=get_setting('MIGASFREE_EXTERNAL_TRAILING_PATH'),
                    suite=deploy.suite,
                    options=deploy.options.replace(' ', '\n') if deploy.options else '',
                )

        return ''
