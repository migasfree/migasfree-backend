# -*- coding: UTF-8 -*-

# Copyright (c) 2015-2020 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2020 Alberto Gacías <alberto@migasfree.org>
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

import os
import subprocess
import tempfile

import django.core.management

from io import StringIO

from django.contrib.auth.models import Group, Permission
from django.contrib.auth.management import create_permissions
from django.apps import apps
from django.conf import settings

from migasfree.core.models import UserProfile


def run(cmd):
    out, err = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        shell=True
    ).communicate()

    return out, err


def configure_user(name, groups=None):
    if groups is None:
        groups = []

    user = UserProfile.objects.filter(username=name)
    if not user:
        user = UserProfile()
        user.username = name
        user.is_staff = True
        user.is_active = True
        user.is_superuser = (name == 'admin')
        user.set_password(name)
        user.save()
    else:
        user = user[0]

    user.groups.clear()
    user.groups.add(*groups)
    user.save()


def add_perms(group, tables=None, all_perms=True):
    if tables is None:
        tables = []

    perms = ['change_%s']
    if all_perms:
        perms.append('add_%s')
        perms.append('delete_%s')

    for table in tables:
        app, name = table.split('.')
        for pattern in perms:
            group.permissions.add(
                Permission.objects.get(
                    codename=pattern % name,
                    content_type__app_label=app
                ).id
            )


def configure_default_users():
    """
    Create/Update default Groups and Users
    """

    # reader group
    reader = Group.objects.filter(name='Reader')
    if not reader:
        reader = Group()
        reader.name = "Reader"
        reader.save()
    else:
        reader = reader[0]

    tables = [
        "client.computer", "client.user", "client.error",
        "client.fault", "client.faultdefinition", "client.migration",
        "client.notification", "client.statuslog",
        "core.attribute", "core.attributeset",
        "core.schedule", "core.scheduledelay",
        "core.project", "core.package", "core.packageset", "client.packagehistory",
        "core.deployment", "core.store", "core.userprofile",
        "core.domain", "core.scope",
        "app_catalog.policy", "app_catalog.policygroup",
        "app_catalog.application", "app_catalog.packagesbyproject",
        "client.synchronization",
        "core.platform", "core.property",
        "device.device", "device.connection", "device.driver",
        "device.manufacturer", "device.feature", "device.logical",
        "device.model", "device.type",
        "hardware.node", "hardware.capability",
        "hardware.configuration", "hardware.logicalname",
    ]
    reader.permissions.clear()
    add_perms(reader, tables, all_perms=False)
    reader.save()

    # liberator group
    liberator = Group.objects.filter(name='Liberator')
    if not liberator:
        liberator = Group()
        liberator.name = "Liberator"
        liberator.save()
    else:
        liberator = liberator[0]

    tables = [
        "core.deployment", "core.schedule", "core.scheduledelay",
        "app_catalog.policy", "app_catalog.policygroup",
        "app_catalog.application", "app_catalog.packagesbyproject",
    ]
    liberator.permissions.clear()
    add_perms(liberator, tables)
    liberator.save()

    # packager group
    packager = Group.objects.filter(name='Packager')
    if not packager:
        packager = Group()
        packager.name = "Packager"
        packager.save()
    else:
        packager = packager[0]

    tables = ["core.package", "core.packageset", "core.store"]
    packager.permissions.clear()
    add_perms(packager, tables)
    packager.save()

    # computer checker group
    checker = Group.objects.filter(name='Computer Checker')
    if not checker:
        checker = Group()
        checker.name = "Computer Checker"
        checker.save()
    else:
        checker = checker[0]

    tables = [
        "client.error", "client.fault", "client.synchronization"
    ]
    checker.permissions.clear()
    add_perms(checker, tables)
    checker.save()

    # device installer group
    device_installer = Group.objects.filter(name='Device installer')
    if not device_installer:
        device_installer = Group()
        device_installer.name = "Device installer"
        device_installer.save()
    else:
        device_installer = device_installer[0]

    tables = [
        "device.connection", "device.manufacturer",
        "device.model", "device.type", "device.device",
        "device.driver", "device.logical",
    ]
    device_installer.permissions.clear()
    add_perms(device_installer, tables)
    device_installer.save()

    # configurator group
    configurator = Group.objects.filter(name='Configurator')
    if not configurator:
        configurator = Group()
        configurator.name = "Configurator"
        configurator.save()
    else:
        configurator = configurator[0]

    tables = [
        "client.faultdefinition", "core.property", "core.project",
        "client.synchronization", "core.platform", "core.attributeset",
        "client.migration", "client.notification",
    ]
    configurator.permissions.clear()
    add_perms(configurator, tables)
    configurator.save()

    # domain admin group
    domain_admin = Group.objects.filter(name='Domain Admin')
    if not domain_admin:
        domain_admin = Group()
        domain_admin.name = "Domain Admin"
        domain_admin.save()
    else:
        domain_admin = domain_admin[0]

    tables = [
        "core.scope", "core.deployment",
    ]
    domain_admin.permissions.clear()
    add_perms(domain_admin, tables)
    add_perms(domain_admin, ["client.computer", ], all_perms=False)
    domain_admin.save()

    # default users
    configure_user("admin")
    configure_user("domain-admin", [reader, domain_admin])
    configure_user("packager", [reader, packager])
    configure_user("configurator", [reader, configurator])
    configure_user("installer", [reader, device_installer])
    configure_user("liberator", [reader, liberator])
    configure_user("checker", [reader, checker])
    configure_user("reader", [reader])
    configure_user("migasfree-play")

    # default user permissions
    user = UserProfile.objects.get(username="migasfree-play")
    user.is_staff = False
    user.save()
    permissions = Permission.objects.filter(
        codename__in=['change_device.logical'],
        content_type__app_label='server'
    )
    user.user_permissions.add(*permissions)


def sequence_reset():
    commands = StringIO()

    os.environ['DJANGO_COLORS'] = 'nocolor'

    label_apps = ['core', 'client', 'device', 'hardware', 'stats', 'app_catalog']
    for label in label_apps:
        django.core.management.call_command(
            'sqlsequencereset',
            label,
            stdout=commands
        )

    if settings.DATABASES.get('default').get('ENGINE') == \
            'django.db.backends.postgresql_psycopg2':
        _filename = tempfile.mkstemp()[1]
        with open(_filename, "w") as _file:
            _file.write(commands.getvalue())
            _file.flush()

        cmd = "su postgres -c 'psql {} -f {}' -".format(
            settings.DATABASES.get('default').get('NAME'),
            _filename
        )
        out, err = run(cmd)
        if out != 0:
            print(err)

        os.remove(_filename)


def create_initial_data():
    perms = Permission.objects.filter(pk=1)
    if not perms:
        for app in apps.get_app_configs():
            create_permissions(app, None, 2)

    configure_default_users()

    fixtures = [
        'core.property.json',
        'core.attribute.json',
        'core.schedule.json',
        'core.schedule_delay.json',
        'client.fault_definition.json',
        'device.type.json',
        'device.feature.json',
        'device.connection.json',
    ]
    for fixture in fixtures:
        app, name, ext = fixture.split('.')
        django.core.management.call_command(
            'loaddata',
            os.path.join(
                settings.MIGASFREE_APP_DIR,
                app,
                'fixtures',
                '{0}.{1}'.format(name, ext)
            ),
            interactive=False,
            verbosity=1
        )
