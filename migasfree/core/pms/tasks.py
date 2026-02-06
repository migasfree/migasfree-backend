# Copyright (c) 2024-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2024-2026 Alberto Gacías <alberto@migasfree.org>
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

import logging
import os
import shutil

import redis
from celery import Celery
from celery.signals import task_postrun

from ...utils import get_setting
from ..decorators import unique_task
from . import get_pms

logger = logging.getLogger('celery')

MIGASFREE_FQDN = get_setting('MIGASFREE_FQDN')
MIGASFREE_PUBLIC_DIR = get_setting('MIGASFREE_PUBLIC_DIR')
MIGASFREE_STORE_TRAILING_PATH = get_setting('MIGASFREE_STORE_TRAILING_PATH')
MIGASFREE_TMP_TRAILING_PATH = get_setting('MIGASFREE_TMP_TRAILING_PATH')

CELERY_BROKER_URL = get_setting('CELERY_BROKER_URL')


app = Celery('migasfree', broker=CELERY_BROKER_URL, backend=CELERY_BROKER_URL, fixups=[])


def symlink(source_path, target_path, name):
    """
    SAMPLE:
    source_path: /var/lib/migasfree-backend/public/prj1/tmp/dists/prj1/PKGS
    target_path: ../../../../stores/org
    name: migasfree-play_1.8.1_amd64.deb
    """

    target = os.path.join(source_path, name)
    if not os.path.lexists(target):
        os.symlink(os.path.join(target_path, name), target)


@app.task
def package_metadata(pms_name, package):
    return get_pms(pms_name).package_metadata(package)


@app.task
def package_info(pms_name, package):
    return get_pms(pms_name).package_info(package)


@app.task(bind=True)
@unique_task(app)
def create_repository_metadata(payload):
    deployment = payload
    project = deployment['project']
    deployment_id = deployment['id']

    pms = get_pms(project['pms'])

    # ADD INFO IN REDIS
    con = redis.from_url(CELERY_BROKER_URL)
    con.hset(f'migasfree:repos:{deployment_id}', mapping={'name': deployment['name'], 'project': project['name']})
    con.sadd('migasfree:watch:repos', deployment_id)

    tmp_path = os.path.join(
        MIGASFREE_PUBLIC_DIR,
        project['slug'],
        os.path.join(MIGASFREE_TMP_TRAILING_PATH, '/'.join(pms.relative_path.split('/')[1:])),
        deployment['slug'],
    )
    stores_path = os.path.join(
        '../' * (len(os.path.join(project['slug'], pms.relative_path).split('/')) + 1), MIGASFREE_STORE_TRAILING_PATH
    )  # IMPORTANT! -> IS RELATIVE

    repository_path = os.path.join(MIGASFREE_PUBLIC_DIR, project['slug'], pms.relative_path, deployment['slug'])

    pkg_tmp_path = os.path.join(tmp_path, pms.components)
    if not os.path.exists(pkg_tmp_path):
        os.makedirs(pkg_tmp_path)

    # Symlinks for packages
    for package in deployment['available_packages']:
        symlink(pkg_tmp_path, os.path.join(stores_path, package['store']['name']), package['fullname'])

    # Metadata in TMP
    logger.info(
        "Creating repository metadata for deployment: '%s' in project: '%s'", deployment['name'], project['name']
    )

    ret, output, error = pms.create_repository(path=tmp_path, arch=project['architecture'])

    # Move from TMP to REPOSITORY
    shutil.rmtree(repository_path, ignore_errors=True)
    shutil.copytree(tmp_path, repository_path, symlinks=True)
    shutil.rmtree(tmp_path)

    # REMOVE INFO IN REDIS
    con.hdel(f'migasfree:repos:{deployment_id}', '*')
    con.srem('migasfree:watch:repos', deployment_id)
    con.close()

    return ret, output if ret == 0 else error, deployment['name'], project['name']


@app.task
def remove_repository_metadata(payload):
    """
    Payload must contain:
    - project: {slug: ..., pms: ...}
    - slug: the deployment slug to remove
    """
    project = payload['project']
    pms = get_pms(project['pms'])
    slug = payload['slug']

    deployment_path = os.path.join(MIGASFREE_PUBLIC_DIR, project['slug'], pms.relative_path, slug)
    if os.path.exists(deployment_path):
        shutil.rmtree(deployment_path, ignore_errors=True)


@task_postrun.connect
def handle_postrun(sender=None, **kwargs):
    if sender == create_repository_metadata:
        if kwargs['state'] == 'SUCCESS':
            ret, output, deployment_name, project_name = kwargs['retval']
            if ret == 0:
                msg = f'Repository metadata for deployment [{deployment_name}] in project [{project_name}] created'
            else:
                msg = (
                    'An error occurred during repository metadata creation'
                    f' for deployment [{deployment_name}]'
                    f' in project [{project_name}]: {output}'
                )
        elif kwargs['state'] == 'REJECTED':
            # Extract info from payload in kwargs
            # kwargs['kwargs'] is {'payload': {...}}
            payload = kwargs.get('kwargs', {}).get('payload', {})
            deployment_id = payload.get('id', 'unknown')

            msg = (
                'Repository metadata creation for deployment ID'
                f' [{deployment_id}] could not be performed.'
                ' Review configuration.'
            )
        elif kwargs['state'] is None:  # REVOKED & TERMINATED
            return

        try:
            # DIRECTLY to Redis - Total Decoupling Mode
            con = redis.from_url(CELERY_BROKER_URL)
            con.lpush('migasfree:notifications:queue', msg)
            con.close()

        except Exception as e_redis:
            logger.error('CRITICAL: Could not push notification to Redis: %s', e_redis)
