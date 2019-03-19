# -*- coding: UTF-8 -*-

# Copyright (c) 2015-2019 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2019 Alberto Gacías <alberto@migasfree.org>
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

from django.conf import settings

from .pms import Pms
from migasfree.utils import execute


class Yum(Pms):
    """
    PMS for yum based systems (Fedora, Red Hat, CentOS, ...)
    """

    def __init__(self):
        self.name = 'yum'
        self.relative_path = 'repos'
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
_DIR=%(path)s/%(name)s
rm -rf $_DIR/repodata
rm -rf $_DIR/checksum
createrepo --cachedir checksum $_DIR
gpg -u migasfree-repository --homedir %(keys_path)s/.gnupg --detach-sign --armor $_DIR/repodata/repomd.xml
        ''' % {
            'path': path,
            'name': os.path.basename(path),
            'keys_path': settings.MIGASFREE_KEYS_DIR
        }

        return execute(_cmd)

    def package_info(self, package):
        """
        string package_info(string package)
        """

        _cmd = '''
echo ****INFO****
rpm -qp --info %(pkg)s
echo
echo
echo ****REQUIRES****
rpm -qp --requires %(pkg)s
echo
echo
echo ****PROVIDES****
rpm -qp --provides %(pkg)s
echo
echo
echo ****OBSOLETES****
rpm -qp --obsoletes %(pkg)s
echo
echo
echo ****SCRIPTS****
rpm -qp --scripts %(pkg)s
echo
echo
echo ****CHANGELOG****
rpm -qp --changelog %(pkg)s
echo
echo
echo ****FILES****
rpm -qp --list %(pkg)s
echo
        ''' % {'pkg': package}

        _ret, _output, _error = execute(_cmd)

        return _output if _ret == 0 else _error

    def source_template(self, deploy):
        """
        string source_template(Deployment deploy)
        """

        from ..models import Deployment

        if deploy.source == Deployment.SOURCE_INTERNAL:
            return """[REPO-{repo}]
name=REPO-{repo}
baseurl={{protocol}}://{{server}}{}/{}/{repo}
enabled=1
http_caching=none
repo_gpgcheck=1
gpgcheck=0
gpgkey=file://{{keys_path}}/{{server}}/repositories.pub
""".format(settings.MEDIA_URL, deploy.project.slug, repo=deploy.slug)
        elif deploy.source == Deployment.SOURCE_EXTERNAL:
            normal_template = """[EXTERNAL-{repo}]
name=EXTERNAL-{repo}
baseurl={{protocol}}://{{server}}{media}{project}/EXTERNAL/{name}/{suite}/$basearch/
{options}
"""
            components_template = """[EXTERNAL-{repo}-{component}]
name=EXTERNAL-{repo}-{component}
baseurl={{protocol}}://{{server}}{media}{project}/EXTERNAL/{name}/{suite}/{component}/$basearch/
{options}
"""
            if deploy.components:
                template = ''
                for component in deploy.components.split(' '):
                    template += components_template.format(
                        repo=deploy.slug,
                        media=settings.MEDIA_URL,
                        project=deploy.project.slug,
                        name=deploy.slug,
                        suite=deploy.suite,
                        options=deploy.options,
                        component=component
                    )

                return template
            else:
                return normal_template.format(
                    repo=deploy.slug,
                    media=settings.MEDIA_URL,
                    project=deploy.project.slug,
                    name=deploy.slug,
                    suite=deploy.suite,
                    options=deploy.options
                )

        return ''
