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
        self.mimetype = ['application/x-rpm', 'application/x-redhat-package-manager']
        self.extensions = ['rpm']
        self.architectures = ['aarch64', 'i386', 'i686', 'noarch', 'x86_64', '(none)']

    def create_repository(self, path, arch):
        """
        (int, string, string) create_repository(
            string path, string arch
        )
        """
        import os
        import shutil

        repodata_dir = os.path.join(path, 'repodata')
        checksum_dir = os.path.join(path, 'checksum')

        shutil.rmtree(repodata_dir, ignore_errors=True)
        shutil.rmtree(checksum_dir, ignore_errors=True)

        ret_create, out_create, err_create = execute(['createrepo', '--cachedir', 'checksum', path], shell=False)
        if ret_create != 0:
            return ret_create, out_create, err_create

        gpg_homedir = os.path.join(self.keys_path, '.gnupg')
        repomd_xml = os.path.join(repodata_dir, 'repomd.xml')

        return execute(
            ['gpg', '-u', 'migasfree-repository', '--homedir', gpg_homedir, '--detach-sign', '--armor', repomd_xml],
            shell=False,
        )

    def package_info(self, package):
        """
        string package_info(string package)
        """
        sections = [
            ('Info', ['--info']),
            ('Requires', ['--requires']),
            ('Provides', ['--provides']),
            ('Obsoletes', ['--obsoletes']),
            ('Scripts', ['--scripts']),
            ('Changelog', ['--changelog']),
            ('Files', ['--list']),
        ]

        output_parts = []
        for section_name, rpm_args in sections:
            ret, out, err = execute(['rpm', '-qp', *rpm_args, package], shell=False)
            if ret != 0:
                if section_name == 'Info':
                    return err or out
                out = err or out

            output_parts.append(f'## {section_name}\n~~~\n{out}~~~\n')

        return '\n'.join(output_parts)

    def package_metadata(self, package):
        """
        dict package_metadata(string package)
        """

        cmd = ['rpm', '-qp', '--queryformat', '%{NAME}___%{VERSION}-%{RELEASE}___%{ARCH}', package]
        ret, output, _error = execute(cmd, shell=False)
        if ret == 0:
            name, version, architecture = output.split('___', 2)
        else:
            name, version, architecture = [None, None, None]

        return {'name': name, 'version': version, 'architecture': architecture}

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
                name=deploy.slug,
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
                        component=component,
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
