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

# TODO check code and test

import logging
import os
import subprocess
import tempfile
from io import StringIO

import django.core.management
from django.apps import apps
from django.conf import settings
from django.contrib.auth.management import create_permissions
from django.contrib.auth.models import Group, Permission

from .core.models import UserProfile

logger = logging.getLogger('migasfree')


def run(cmd):
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True) as process:
        out, err = process.communicate()

        return out, err


def configure_user(name, groups=None):
    user, _ = UserProfile.objects.get_or_create(username=name)

    user.username = name
    user.is_staff = True
    user.is_active = True
    user.is_superuser = name == 'admin'
    user.set_password(name)
    user.save()

    if groups is not None:
        user.groups.set(groups)
    else:
        user.groups.clear()

    user.save()


def add_perms(group, tables=None, perms='all'):
    if tables is None:
        tables = []

    if perms == 'all':
        perms = ['add', 'view', 'change', 'delete']

    for table in tables:
        app, name = table.split('.')
        for item in perms:
            group.permissions.add(
                Permission.objects.filter(codename=f'{item}_{name}', content_type__app_label=app).first().id
            )


def configure_default_users():
    """
    Create/Update default Groups and Users
    """

    # reader group
    reader, _ = Group.objects.get_or_create(name='Reader')
    reader.name = 'Reader'
    reader.save()

    tables = [
        'client.computer',
        'client.user',
        'client.error',
        'client.fault',
        'client.faultdefinition',
        'client.migration',
        'client.notification',
        'client.statuslog',
        'core.attribute',
        'core.attributeset',
        'core.schedule',
        'core.scheduledelay',
        'core.project',
        'core.package',
        'core.packageset',
        'client.packagehistory',
        'core.deployment',
        'core.store',
        'core.userprofile',
        'core.domain',
        'core.scope',
        'app_catalog.policy',
        'app_catalog.policygroup',
        'app_catalog.application',
        'app_catalog.packagesbyproject',
        'client.synchronization',
        'core.platform',
        'core.property',
        'device.device',
        'device.connection',
        'device.driver',
        'device.manufacturer',
        'device.capability',
        'device.logical',
        'device.model',
        'device.type',
        'hardware.node',
        'hardware.capability',
        'hardware.configuration',
        'hardware.logicalname',
    ]
    reader.permissions.clear()
    add_perms(reader, tables, perms=['view'])
    reader.save()

    # liberator group
    liberator, _ = Group.objects.get_or_create(name='Liberator')
    liberator.name = 'Liberator'
    liberator.save()

    tables = [
        'core.deployment',
        'core.schedule',
        'core.scheduledelay',
        'app_catalog.policy',
        'app_catalog.policygroup',
        'app_catalog.application',
        'app_catalog.packagesbyproject',
    ]
    liberator.permissions.clear()
    add_perms(liberator, tables)
    add_perms(liberator, ['client.notification'], perms=['add'])
    liberator.save()

    # packager group
    packager, _ = Group.objects.get_or_create(name='Packager')
    packager.name = 'Packager'
    packager.save()

    packager.permissions.clear()
    add_perms(packager, ['core.package', 'core.packageset', 'core.store'])
    packager.save()

    # computer checker group
    checker, _ = Group.objects.get_or_create(name='Computer Checker')
    checker.name = 'Computer Checker'
    checker.save()

    checker.permissions.clear()
    add_perms(checker, ['client.error', 'client.fault', 'client.synchronization'])
    checker.save()

    # device installer group
    device_installer, _ = Group.objects.get_or_create(name='Device installer')
    device_installer.name = 'Device installer'
    device_installer.save()

    tables = [
        'device.connection',
        'device.manufacturer',
        'device.model',
        'device.type',
        'device.device',
        'device.driver',
        'device.logical',
    ]
    device_installer.permissions.clear()
    add_perms(device_installer, tables)
    device_installer.save()

    # configurator group
    configurator, _ = Group.objects.get_or_create(name='Configurator')
    configurator.name = 'Configurator'
    configurator.save()

    tables = [
        'client.faultdefinition',
        'core.property',
        'core.project',
        'client.synchronization',
        'core.platform',
        'core.attributeset',
        'client.migration',
        'client.notification',
    ]
    configurator.permissions.clear()
    add_perms(configurator, tables)
    configurator.save()

    # domain admin group
    domain_admin, _ = Group.objects.get_or_create(name='Domain Admin')
    domain_admin.name = 'Domain Admin'
    domain_admin.save()

    domain_admin.permissions.clear()
    add_perms(domain_admin, ['core.scope', 'core.deployment'])
    add_perms(domain_admin, ['client.computer'], perms=['view'])
    domain_admin.save()

    # default users
    configure_user('admin')
    configure_user('domain-admin', [reader, domain_admin])
    configure_user('packager', [reader, packager])
    configure_user('configurator', [reader, configurator])
    configure_user('installer', [reader, device_installer])
    configure_user('liberator', [reader, liberator])
    configure_user('checker', [reader, checker])
    configure_user('reader', [reader])

    configure_user('migasfree-play')

    # default user permissions
    user = UserProfile.objects.get(username='migasfree-play')
    user.is_staff = False
    user.save()
    permissions = Permission.objects.filter(codename__in=['change_logical'], content_type__app_label='device')
    user.user_permissions.add(*permissions)


def sequence_reset():
    commands = StringIO()

    os.environ['DJANGO_COLORS'] = 'nocolor'

    label_apps = ['core', 'client', 'device', 'hardware', 'stats', 'app_catalog']
    for label in label_apps:
        django.core.management.call_command('sqlsequencereset', label, stdout=commands)

    if settings.DATABASES.get('default').get('ENGINE') == 'django.db.backends.postgresql_psycopg2':
        _filename = tempfile.mkstemp()[1]
        with open(_filename, 'w', encoding='utf-8') as _file:
            _file.write(commands.getvalue())
            _file.flush()

        cmd = "su postgres -c 'psql {} -f {}' -".format(settings.DATABASES.get('default').get('NAME'), _filename)
        out, err = run(cmd)
        if out != 0:
            logger.error('Error resetting sequences: %s', err)

        os.remove(_filename)


def create_initial_data():
    perms = Permission.objects.filter(pk=1)
    if not perms.exists():
        for app in apps.get_app_configs():
            create_permissions(app, verbosity=2)

    configure_default_users()

    fixtures = [
        'app_catalog.category.json',
        'core.property.json',
        'core.attribute.json',
        'core.schedule.json',
        'core.schedule_delay.json',
        'client.fault_definition.json',
        'device.type.json',
        'device.capability.json',
        'device.connection.json',
    ]
    for fixture in fixtures:
        app, name, ext = fixture.split('.')
        django.core.management.call_command(
            'loaddata', os.path.join(settings.MIGASFREE_APP_DIR, app, 'fixtures', f'{name}.{ext}'), verbosity=1
        )
