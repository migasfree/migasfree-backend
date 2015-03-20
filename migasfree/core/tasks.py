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

from .models import Repository


@shared_task(queue='repository')
def remove_repository_metadata(repo_id, old_slug=''):
    try:
        repo = Repository.objects.get(id=repo_id)
    except:
        raise Ignore()

    if old_slug:
        slug = old_slug
    else:
        slug = repo.slug

    mod = import_module('migasfree.core.pms.%s' % repo.project.pms)
    pms = getattr(mod, repo.project.pms.capitalize())()

    destination = os.path.join(
        settings.MIGASFREE_PUBLIC_DIR,
        repo.project.slug,
        pms.relative_path,
        slug
    )
    shutil.rmtree(destination, ignore_errors=True)


@shared_task(queue='repository')
def create_repository_metadata(repo_id):
    try:
        repo = Repository.objects.get(id=repo_id)
    except:
        raise Ignore()

    con = get_redis_connection('default')
    con.hmset(
        'migasfree:repos:%d' % repo.id, {
            'name': repo.name,
            'project': repo.project.name
        }
    )
    con.sadd('migasfree:watch:repos', repo.id)

    mod = import_module('migasfree.core.pms.%s' % repo.project.pms)
    pms = getattr(mod, repo.project.pms.capitalize())()

    tmp_path = os.path.join(
        settings.MIGASFREE_PUBLIC_DIR,
        repo.project.slug,
        'tmp'
    )
    stores_path = os.path.join(
        settings.MIGASFREE_PUBLIC_DIR,
        repo.project.slug,
        'stores'
    )
    _slug_tmp_path = os.path.join(
        settings.MIGASFREE_PUBLIC_DIR,
        repo.project.slug,
        'tmp',
        pms.relative_path
    )

    if _slug_tmp_path.endswith('/'):
        # remove trailing slash for replacing in template
        _slug_tmp_path = _slug_tmp_path[:-1]

    pkg_tmp_path = os.path.join(
        _slug_tmp_path,
        repo.slug,
        'PKGS'
    )
    if not os.path.exists(pkg_tmp_path):
        os.makedirs(pkg_tmp_path)

    for pkg_id in repo.available_packages.values_list('id', flat=True):
        pkg = Package.objects.get(id=pkg_id)
        dst = os.path.join(slug_tmp_path, repo.slug, 'PKGS', pkg.name)
        if not os.path.lexists(dst):
            os.symlink(
                os.path.join(stores_path, pkg.store.slug, pkg.name),
                dst
            )

    ret, output, error = pms.create_repository(
        repo.slug, _slug_tmp_path
    )

    source = os.path.join(
        tmp_path,
        pms.relative_path,
        repo.slug
    )
    target = os.path.join(
        settings.MIGASFREE_PUBLIC_DIR,
        repo.project.slug,
        pms.relative_path,
        repo.slug
    )
    shutil.rmtree(target, ignore_errors=True)
    shutil.copytree(source, target, symlinks=True)
    shutil.rmtree(tmp_path)

    con.hdel('migasfree:repos:%d' % repo.id, '*')
    con.srem('migasfree:watch:repos', repo.id)

    return (ret, output if ret == 0 else error)
