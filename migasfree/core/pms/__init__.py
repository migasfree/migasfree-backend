# -*- coding: utf-8 -*-

# Copyright (c) 2015-2024 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2024 Alberto Gacías <alberto@migasfree.org>
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

import sys
import inspect
import importlib
import pkgutil

import migasfree.core.pms.plugins

from importlib import import_module

from .apt import Apt
from .dnf import Dnf
from .pacman import Pacman
from .winget import Winget
from .wpt import Wpt
from .yum import Yum
from .zypper import Zypper


def iter_namespace(ns_pkg):
    return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + '.')


def get_discovered_plugins():
    return {
        name: importlib.import_module(name)
        for finder, name, ispkg
        in iter_namespace(migasfree.core.pms.plugins)
    }


def get_available_pms():
    ret = [
        ('apt', 'apt'),
        ('dnf', 'dnf'),
        ('pacman', 'pacman'),
        ('winget', 'winget'),
        ('wpt', 'wpt'),
        ('yum', 'yum'),
        ('zypper', 'zypper'),
    ]

    discovered_plugins = get_discovered_plugins()
    for item in discovered_plugins.keys():
        pms = item.split('.')[-1]
        ret.append((pms, f'plugins.{pms}'))

    return tuple(sorted(ret, key=lambda x: x[0]))


def get_available_mimetypes():
    ret = Apt().mimetype + Dnf().mimetype + Pacman().mimetype \
        + Winget().mimetype + Wpt().mimetype + Yum().mimetype + Zypper().mimetype

    discovered_plugins = get_discovered_plugins()
    for item in discovered_plugins.keys():
        for class_ in inspect.getmembers(sys.modules[item], inspect.isclass):
            if class_[0] != 'Pms':
                ret += class_[1]().mimetype

    return ';'.join(ret)


def get_pms(name):
    available_pms = dict(get_available_pms())
    mod = import_module(
        f'migasfree.core.pms.{available_pms.get(name)}'
    )

    return getattr(mod, name.capitalize())()
