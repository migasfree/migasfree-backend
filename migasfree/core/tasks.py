# -*- coding: utf-8 -*-

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
import shutil

from celery import shared_task
from celery.exceptions import Ignore
from django_redis import get_redis_connection
from django.core.exceptions import ObjectDoesNotExist

from .models import Deployment, Store


@shared_task(queue='repository')
def remove_repository_metadata(deployment_id, old_slug=''):
    try:
        deploy = Deployment.objects.get(id=deployment_id)
    except ObjectDoesNotExist:
        raise Ignore()

    if old_slug:
        slug = old_slug
    else:
        slug = deploy.slug

    shutil.rmtree(deploy.path(slug), ignore_errors=True)


def symlink_pkg(pkg, source_path, target_path):
    target = os.path.join(target_path, pkg.fullname)
    if not os.path.lexists(target):
        os.symlink(
            os.path.join(source_path, pkg.store.slug, pkg.fullname),
            target
        )


@shared_task(queue='repository')
def create_repository_metadata(deployment_id):
    try:
        deploy = Deployment.objects.get(id=deployment_id)
    except:
        raise Ignore()

    con = get_redis_connection()
    con.hmset(
        'migasfree:repos:%d' % deploy.id, {
            'name': deploy.name,
            'project': deploy.project.name
        }
    )
    con.sadd('migasfree:watch:repos', deploy.id)

    tmp_path = deploy.path('tmp')
    stores_path = Store.path(deploy.project.slug, '')[:-1]  # remove trailing slash
    slug_tmp_path = os.path.join(
        tmp_path,
        deploy.pms().relative_path
    )

    if slug_tmp_path.endswith('/'):
        # remove trailing slash for replacing in template
        slug_tmp_path = slug_tmp_path[:-1]

    pkg_tmp_path = os.path.join(
        slug_tmp_path,
        deploy.slug,
        'PKGS'  # FIXME hardcoded path!!!
    )
    if not os.path.exists(pkg_tmp_path):
        os.makedirs(pkg_tmp_path)

    for pkg in deploy.available_packages.all():
        symlink_pkg(pkg, stores_path, pkg_tmp_path)

    for set_ in deploy.available_package_sets.all():
        for pkg in set_.packages.all():
            symlink_pkg(pkg, stores_path, pkg_tmp_path)

    source = os.path.join(slug_tmp_path, deploy.slug)
    ret, output, error = deploy.pms().create_repository(
        path=source,
        arch=deploy.project.architecture
    )

    target = deploy.path()
    shutil.rmtree(target, ignore_errors=True)

    shutil.copytree(source, target, symlinks=True)
    shutil.rmtree(tmp_path)

    con.hdel('migasfree:repos:%d' % deploy.id, '*')
    con.srem('migasfree:watch:repos', deploy.id)

    return ret, output if ret == 0 else error
