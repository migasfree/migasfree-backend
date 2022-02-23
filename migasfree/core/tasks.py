# -*- coding: utf-8 -*-

# Copyright (c) 2015-2022 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2022 Alberto Gacías <alberto@migasfree.org>
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
import redis
import requests

from celery import Celery
from celery.exceptions import Ignore

from .pms import get_pms

from ..utils import get_secret, get_setting

MIGASFREE_FQDN = get_setting('MIGASFREE_FQDN')
MIGASFREE_PUBLIC_DIR = get_setting('MIGASFREE_PUBLIC_DIR')
MIGASFREE_STORE_TRAILING_PATH = get_setting('MIGASFREE_STORE_TRAILING_PATH')
MIGASFREE_TMP_TRAILING_PATH = get_setting('MIGASFREE_TMP_TRAILING_PATH')

REDIS_HOST = get_setting('REDIS_HOST')
REDIS_PORT = get_setting('REDIS_PORT')
REDIS_DB = get_setting('REDIS_DB')

BROKER_URL = get_setting('BROKER_URL')

AUTH_TOKEN = f'Token {get_secret("token_admin")}'

API_URL = f'http://{MIGASFREE_FQDN}/api/v1/token'

REQUESTS_OK_CODES = [
    requests.codes.ok, requests.codes.created,
    requests.codes.moved, requests.codes.found,
    requests.codes.temporary_redirect, requests.codes.resume
]

app = Celery('migasfree', broker=BROKER_URL, backend=BROKER_URL)


def symlink(source_path, target_path, name):
    """
    SAMPLE:
    source_path: /var/lib/migasfree-backend/public/prj1/tmp/dists/prj1/PKGS
    target_path: ../../../../stores/org
    name: migasfree-play_1.8.1_amd64.deb
    """

    target = os.path.join(source_path, name)
    if not os.path.lexists(target):
        os.symlink(
            os.path.join(target_path, name),
            target
        )


@app.task
def package_metadata(pms_name, package):
    return get_pms(pms_name).package_metadata(package)


@app.task
def package_info(pms_name, package):
    return get_pms(pms_name).package_info(package)


@app.task
def create_repository_metadata(deployment_id):
    req = requests.get(
        f'{API_URL}/deployments/{deployment_id}/',
        headers={'Authorization': AUTH_TOKEN}
    )

    if req.status_code not in REQUESTS_OK_CODES:
        raise Ignore()

    deployment = req.json()
    project = deployment["project"]

    pms = get_pms(project["pms"])

    # ADD INFO IN REDIS
    con = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    con.hmset(
        'migasfree:repos:%d' % deployment_id, {
            'name': deployment["name"],
            'project': project["name"]
        }
    )
    con.sadd('migasfree:watch:repos', deployment_id)

    tmp_path = os.path.join(
        MIGASFREE_PUBLIC_DIR,
        project["slug"],
        os.path.join(
            MIGASFREE_TMP_TRAILING_PATH,
            "/".join(pms.relative_path.split("/")[1:])
        ),
        deployment["slug"]
    )
    stores_path = os.path.join(
        "../" * (len(os.path.join(project["slug"], pms.relative_path).split("/")) + 1),
        MIGASFREE_STORE_TRAILING_PATH
    )  # IMPORTANT! -> IS RELATIVE

    repository_path = os.path.join(
        MIGASFREE_PUBLIC_DIR,
        project["slug"],
        pms.relative_path,
        deployment["slug"]
    )

    pkg_tmp_path = os.path.join(tmp_path, pms.components)
    if not os.path.exists(pkg_tmp_path):
        os.makedirs(pkg_tmp_path)

    # Packages
    packages = deployment["available_packages"]

    # Package Sets
    for package_set in deployment["available_package_sets"]:
        req = requests.get(
            f'{API_URL}/package-sets/{package_set["id"]}/',
            headers={'Authorization': AUTH_TOKEN}
        )
        if req.status_code in REQUESTS_OK_CODES:
            # concatenates packages
            packages = [*packages, *req.json()["packages"]]

    # Symlinks for packages
    for package in packages:
        req = requests.get(
            f'{API_URL}/packages/{package["id"]}/',
            headers={'Authorization': AUTH_TOKEN}
        )
        if req.status_code in REQUESTS_OK_CODES:
            symlink(
                pkg_tmp_path,
                os.path.join(stores_path, req.json()["store"]["name"]),
                package["fullname"]
            )

    # Metadata in TMP
    print("Creating repository metadata for deployment: '{}' in project: '{}'".format(
        deployment["name"], project["name"]
    ))  # DEBUG

    ret, output, error = pms.create_repository(path=tmp_path, arch=project["architecture"])
    print(output if ret == 0 else error)  # DEBUG

    # Move from TMP to REPOSITORY
    shutil.rmtree(repository_path, ignore_errors=True)
    shutil.copytree(tmp_path, repository_path, symlinks=True)
    shutil.rmtree(tmp_path)

    # REMOVE INFO IN REDIS
    con.hdel('migasfree:repos:%d' % deployment_id, '*')
    con.srem('migasfree:watch:repos', deployment_id)
    con.close()

    return ret, output if ret == 0 else error


@app.task
def remove_repository_metadata(deployment_id, old_slug=''):
    req = requests.get(
        f'{API_URL}/deployments/{deployment_id}/',
        headers={'Authorization': AUTH_TOKEN}
    )

    if req.status_code not in REQUESTS_OK_CODES:
        raise Ignore()

    deployment = req.json()
    project = deployment["project"]
    pms = get_pms(project["pms"])

    if old_slug:
        slug = old_slug
    else:
        slug = deployment["slug"]

    deployment_path = os.path.join(
        MIGASFREE_PUBLIC_DIR,
        project["slug"],
        pms.relative_path,
        slug
    )
    shutil.rmtree(deployment_path, ignore_errors=True)
