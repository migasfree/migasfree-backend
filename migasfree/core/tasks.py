# -*- coding: utf-8 -*-

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

from __future__ import absolute_import

import os
import shutil

from celery import shared_task
from celery.exceptions import Ignore
from django_redis import get_redis_connection
from django.conf import settings
from importlib import import_module

from .models import Release, Package


@shared_task(queue='repository')
def remove_repository_metadata(release_id, old_slug=''):
    try:
        release = Release.objects.get(id=release_id)
    except:
        raise Ignore()

    if old_slug:
        slug = old_slug
    else:
        slug = release.slug

    mod = import_module('migasfree.core.pms.%s' % release.project.pms)
    pms = getattr(mod, release.project.pms.capitalize())()

    destination = os.path.join(
        settings.MIGASFREE_PUBLIC_DIR,
        release.project.slug,
        pms.relative_path,
        slug
    )
    shutil.rmtree(destination, ignore_errors=True)


@shared_task(queue='repository')
def create_repository_metadata(release_id):
    try:
        release = Release.objects.get(id=release_id)
    except:
        raise Ignore()

    con = get_redis_connection('default')
    con.hmset(
        'migasfree:repos:%d' % release.id, {
            'name': release.name,
            'project': release.project.name
        }
    )
    con.sadd('migasfree:watch:repos', release.id)

    mod = import_module('migasfree.core.pms.%s' % release.project.pms)
    pms = getattr(mod, release.project.pms.capitalize())()

    tmp_path = os.path.join(
        settings.MIGASFREE_PUBLIC_DIR,
        release.project.slug,
        'tmp'
    )
    stores_path = os.path.join(
        settings.MIGASFREE_PUBLIC_DIR,
        release.project.slug,
        'stores'
    )
    slug_tmp_path = os.path.join(
        settings.MIGASFREE_PUBLIC_DIR,
        release.project.slug,
        'tmp',
        pms.relative_path
    )

    if slug_tmp_path.endswith('/'):
        # remove trailing slash for replacing in template
        slug_tmp_path = slug_tmp_path[:-1]

    pkg_tmp_path = os.path.join(
        slug_tmp_path,
        release.slug,
        'PKGS'
    )
    if not os.path.exists(pkg_tmp_path):
        os.makedirs(pkg_tmp_path)

    for pkg_id in release.available_packages.values_list('id', flat=True):
        pkg = Package.objects.get(id=pkg_id)
        dst = os.path.join(slug_tmp_path, release.slug, 'PKGS', pkg.name)
        if not os.path.lexists(dst):
            os.symlink(
                os.path.join(stores_path, pkg.store.slug, pkg.name),
                dst
            )

    ret, output, error = pms.create_repository(
        release.slug, slug_tmp_path, release.project.architecture
    )

    source = os.path.join(
        tmp_path,
        pms.relative_path,
        release.slug
    )
    target = os.path.join(
        settings.MIGASFREE_PUBLIC_DIR,
        release.project.slug,
        pms.relative_path,
        release.slug
    )
    shutil.rmtree(target, ignore_errors=True)
    shutil.copytree(source, target, symlinks=True)
    shutil.rmtree(tmp_path)

    con.hdel('migasfree:repos:%d' % release.id, '*')
    con.srem('migasfree:watch:repos', release.id)

    return (ret, output if ret == 0 else error)
