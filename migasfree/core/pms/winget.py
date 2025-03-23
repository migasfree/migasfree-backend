# -*- coding: UTF-8 -*-

# Copyright (c) 2021-2025 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2021-2025 Alberto Gacías <alberto@migasfree.org>
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
import sqlite3
import shutil

from ...utils import execute, get_setting, read_file, write_file

from .pms import Pms

try:
    import yaml
except ImportError:
    pass


def get_id(con, cursor, table, field, value):
    cursor.execute(f'SELECT rowid FROM {table} WHERE {field} = "{value}";')
    con.commit()

    row = cursor.fetchall()
    if len(row) == 0:
        cursor.execute(f'SELECT MAX(rowid) + 1 FROM {table}')
        con.commit()

        id_ = cursor.fetchall()[0][0]
        if not id_:
            id_ = 1

        cursor.execute(
            f'INSERT INTO {table} (rowid, {field}) VALUES (?,?)',
            (id_, value)
        )
        con.commit()

        return id_

    return row[0][0]


def normalize(name):
    return name.replace(' ', '').lower()


class Winget(Pms):
    """
    PMS for winget (Microsoft Windows)
    """

    def __init__(self):
        super().__init__()

        self.name = 'winget'
        self.relative_path = get_setting('MIGASFREE_REPOSITORY_TRAILING_PATH')
        self.mimetype = ['application/yaml']
        self.extensions = ['yaml']

    def create_repository(self, path, arch):
        """
        (int, string, string) create_repository(
            string path, string arch
        )
        """

        # Copy Files from template (included in container!!!)
        try:
            shutil.copytree(
                '/source.template/Assets',
                os.path.join(path, 'source', 'Assets')
            )
        except shutil.Error:
            pass

        try:
            shutil.copytree(
                '/source.template/Public',
                os.path.join(path, 'source', 'Public')
            )
        except shutil.Error:
            pass

        try:
            shutil.copyfile(
                '/source.template/AppxManifest.xml',
                os.path.join(path, 'source', 'AppxManifest.xml')
            )
        except (shutil.Error, shutil.SameFileError):
            pass

        con = sqlite3.connect(os.path.join(path, 'source', 'Public', 'index.db'))
        cursor = con.cursor()

        cursor.execute('DELETE FROM ids;')
        cursor.execute('DELETE FROM monikers;')
        cursor.execute('DELETE FROM names;')
        cursor.execute('DELETE FROM versions;')
        cursor.execute('DELETE FROM pathparts;')
        cursor.execute('DELETE FROM manifest;')
        cursor.execute('DELETE FROM tags;')
        cursor.execute('DELETE FROM tags_map;')
        cursor.execute('DELETE FROM commands;')
        cursor.execute('DELETE FROM commands_map;')
        cursor.execute('DELETE FROM pfns;')
        cursor.execute('DELETE FROM pfns_map;')
        cursor.execute('DELETE FROM productcodes;')
        cursor.execute('DELETE FROM productcodes_map;')
        cursor.execute('DELETE FROM norm_names;')
        cursor.execute('DELETE FROM norm_names_map;')
        cursor.execute('DELETE FROM norm_publishers;')
        cursor.execute('DELETE FROM norm_publishers_map;')

        # CREATE SQLITE DATABASE
        manifest = 1

        cursor.execute(
            'INSERT INTO pathparts (rowid, pathpart) VALUES (?,?)',
            (1, self.components)
        )
        con.commit()

        _pkgs_path = os.path.join(path, self.components)
        for package in os.listdir(_pkgs_path):
            if package.endswith(".yaml"):
                with open(os.path.join(_pkgs_path, package), 'r') as stream:
                    try:
                        data = yaml.safe_load(stream)
                        print('processing', data['PackageIdentifier'], data['PackageVersion'])
                    except yaml.YAMLError as exc:
                        print(exc)

                    # IDS
                    id_ = get_id(con, cursor, 'ids', 'id', data['PackageIdentifier'])

                    # NAMES
                    if 'PackageName' not in data:
                        data['PackageName'] = data['PackageIdentifier'].split('.')[-1]

                    name = get_id(con, cursor, 'names', 'name', data['PackageName'])

                    # MONIKERS
                    if 'Moniker' not in data:
                        data['Moniker'] = data['PackageName']

                    moniker = get_id(con, cursor, 'monikers', 'moniker', data['Moniker'])

                    # VERSION
                    version = get_id(con, cursor, 'versions', 'version', data['PackageVersion'])

                    # PATHPARTS
                    pathpart = get_id(con, cursor, 'pathparts', 'pathpart', package)
                    cursor.execute(f'UPDATE pathparts SET parent=1 WHERE rowid={pathpart};')
                    con.commit()

                    # MANIFEST
                    cursor.execute(
                        'INSERT INTO manifest (rowid, id, name, moniker, version, channel, pathpart) '
                        'VALUES (?,?,?,?,?,?,?)',
                        (manifest, id_, name, moniker, version, 1, pathpart)
                    )
                    con.commit()

                    # NORM_NAMES
                    norm_name = get_id(con, cursor, 'norm_names', 'norm_name', normalize(data['PackageName']))
                    cursor.execute(
                        'INSERT INTO norm_names_map (manifest, norm_name) VALUES (?,?)',
                        (manifest, norm_name)
                    )
                    con.commit()

                    # NORM_PUBLISHERS
                    if 'Publisher' not in data:
                        data['Publisher'] = data['PackageIdentifier'].split('.')[0]
                    norm_publisher = get_id(
                        con, cursor, 'norm_publishers', 'norm_publisher',
                        normalize(data['Publisher'])
                    )
                    cursor.execute(
                        'INSERT INTO norm_publishers_map (manifest, norm_publisher) VALUES (?,?)',
                        (manifest, norm_publisher)
                    )
                    con.commit()

                    # TAGS
                    if 'Tags' in data:
                        for _tag in data['Tags']:
                            tag = get_id(con, cursor, 'tags', 'tag', _tag)
                            cursor.execute('INSERT INTO tags_map (manifest, tag) VALUES (?,?)', (manifest, tag))
                            con.commit()

                    # COMMANDS
                    if 'Commands' in data:
                        for _command in data['Commands']:
                            command = get_id(con, cursor, 'commands', 'command', _command)
                            cursor.execute(
                                'INSERT INTO commands_map (manifest, command) VALUES (?,?)',
                                (manifest, command)
                            )
                            con.commit()

                    # PFNS
                    if 'Installers' in data:
                        if 'PackageFamilyName' in data['Installers'][0]:
                            pfn = get_id(con, cursor, 'pfns', 'pfn', data['Installers'][0]['PackageFamilyName'])
                            cursor.execute('INSERT INTO pfns_map (manifest, pfn) VALUES (?,?)', (manifest, pfn))
                            con.commit()

                        # PRODUCTCODES
                        if 'ProductCode' in data['Installers'][0]:
                            productcode = get_id(
                                con, cursor, 'productcodes', 'productcode',
                                data['Installers'][0]['ProductCode']
                            )
                            cursor.execute(
                                'INSERT INTO productcodes_map (manifest, productcode) VALUES (?,?)',
                                (manifest, productcode)
                            )
                            con.commit()

                    manifest += 1

        con.close()

        # Process AppxManifest.xml
        appxmanifest_file = os.path.join(path, 'source', 'AppxManifest.xml')
        appx = read_file(appxmanifest_file).decode('utf-8')

        # REVERSED SUBJECT IS NECCESARY!!!
        subject = ','.join(
            reversed(get_setting('MIGASFREE_CERTIFICATE_SUBJECT').split(','))
        ).strip().replace('ST =', 'S =').replace(' = ', '=')

        context = {
            'fqdn': get_setting('FQDN'),
            'source': os.path.basename(path),
            'subject':  subject
        }

        appx = appx.format(**context)
        write_file(appxmanifest_file, appx)

        # CREATES MSIX & SIGN IT
        _cmd = '''
cd %(path)s
makemsix pack -d %(path)s/source -p %(path)s/source.msix
rm -rf %(path)s/source
makemsix sign -p %(path)s/source.msix -c %(certificates_path)s/cert.pfx -cf PFX
if [ $? = 0 ]
then
   echo "*****    %(name)s/source.msix is signed OK ****"
else
   echo "*****    ERROR: %(name)s/source.msix is not signed****"
fi
''' % {
            'path': path,
            'name': os.path.basename(path),
            'certificates_path': get_setting('MIGASFREE_CERTIFICATES_DIR')
        }

        return execute(_cmd)

    def package_info(self, package):
        """
        string package_info(string package)
        """

        return read_file(package).decode()

    def package_metadata(self, package):
        """
        dict package_metadata(string package)
        """

        with open(package, 'r') as stream:
            try:
                data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        name = data['PackageIdentifier']
        version = data['PackageVersion']
        architecture = 'x64'

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
            return '{name} {{protocol}}://{{server}}{media_url}{project}/{trailing_path}/{name}'.format(
                media_url=self.media_url,
                project=deploy.project.slug,
                trailing_path=get_setting('MIGASFREE_REPOSITORY_TRAILING_PATH'),
                name=deploy.slug,
            )
        elif deploy.source == Deployment.SOURCE_EXTERNAL:
            return '{name} {{protocol}}://{{server}}/src/{project}/{trailing_path}/{name}'.format(
                project=deploy.project.slug,
                trailing_path=get_setting('MIGASFREE_EXTERNAL_TRAILING_PATH'),
                name=deploy.slug,
            )

        return ''
