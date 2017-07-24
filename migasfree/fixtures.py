# -*- coding: UTF-8 -*-

# Copyright (c) 2015-2017 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2017 Alberto Gacías <alberto@migasfree.org>
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

from StringIO import StringIO

from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.management import create_permissions
from django.apps import apps
from django.conf import settings


def run(cmd):
    out, err = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        shell=True
    ).communicate()

    return out, err


def create_user(name, groups=None):
    if groups is None:
        groups = []

    user = User.objects.filter(username=name)
    if not user:
        user = User()
        user.username = name
        user.is_staff = True
        user.is_active = True
        user.is_superuser = (name == 'admin')
        user.set_password(name)
        user.save()

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


def create_default_users():
    """
    Create default Groups and Users
    """

    # reader group
    reader = Group.objects.filter(name='Reader')
    if not reader:
        reader = Group()
        reader.name = "Reader"
        reader.save()
        tables = [
            "client.computer", "client.user", "core.attribute", "client.error",
            "core.schedule", "core.scheduledelay",
            "client.fault", "client.faultdefinition", "client.migration",
            "client.notification",
            "core.project", "core.package", "core.packageset", "client.packagehistory",
            "core.deployment", "core.store",
            "app_catalog.policy", "app_catalog.policygroup",
            "app_catalog.application", "app_catalog.packagesbyproject",
            "client.synchronization",
            "core.platform", "core.property",
            "device.device", "device.connection", "device.manufacturer",
            "device.model", "device.type",
        ]
        add_perms(reader, tables, all_perms=False)
        reader.save()

    # liberator group
    liberator = Group.objects.filter(name='Liberator')
    if not liberator:
        liberator = Group()
        liberator.name = "Liberator"
        liberator.save()
        tables = [
            "core.deployment", "core.schedule", "core.scheduledelay",
            "app_catalog.policy", "app_catalog.policygroup",
        ]
        add_perms(liberator, tables)
        liberator.save()

    # packager group
    packager = Group.objects.filter(name='Packager')
    if not packager:
        packager = Group()
        packager.name = "Packager"
        packager.save()
        tables = ["core.package", "core.packageset", "core.store"]
        add_perms(packager, tables)
        packager.save()

    # computer checker group
    checker = Group.objects.filter(name='Computer Checker')
    if not checker:
        checker = Group()
        checker.name = "Computer Checker"
        checker.save()
        tables = [
            "client.error", "client.fault", "client.synchronization"
        ]
        add_perms(checker, tables)
        checker.save()

    # device installer group
    device_installer = Group.objects.filter(name='Device installer')
    if not device_installer:
        device_installer = Group()
        device_installer.name = "Device installer"
        device_installer.save()
        tables = [
            "device.connection", "device.manufacturer",
            "device.model", "device.type"
        ]
        add_perms(device_installer, tables)
        device_installer.save()

    # configurator group
    configurator = Group.objects.filter(name='Configurator')
    if not configurator:
        configurator = Group()
        configurator.name = "Configurator"
        configurator.save()
        tables = [
            "client.faultdefinition", "core.property", "core.project",
            "client.synchronization", "core.platform",
            "client.migration", "client.notification",
        ]
        add_perms(configurator, tables)
        configurator.save()

    # default users
    create_user("admin")
    create_user("packager", [reader, packager])
    create_user("configurator", [reader, configurator])
    create_user("installer", [reader, device_installer])
    create_user("liberator", [reader, liberator])
    create_user("checker", [reader, checker])
    create_user("reader", [reader])


def sequence_reset():
    commands = StringIO()

    os.environ['DJANGO_COLORS'] = 'nocolor'
    django.core.management.call_command(
        'sqlsequencereset',
        'core client device hardware',
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

    create_default_users()

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
