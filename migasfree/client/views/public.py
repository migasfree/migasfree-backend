# -*- coding: utf-8 *-*

# Copyright (c) 2015-2023 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2023 Alberto Gacías <alberto@migasfree.org>
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

from django.conf import settings
from django.contrib import auth
from django.utils.translation import gettext, gettext_lazy as _
from django.http import HttpResponseForbidden
from rest_framework import views, status
from rest_framework.response import Response

from ...core.models import Platform, Project
from ...core.pms import get_available_pms
from ...secure import create_server_keys, generate_rsa_keys, gpg_get_key
from ...utils import get_client_ip, read_file

from .. import permissions, models


def get_platform_or_create(platform_name, ip_address=None):
    platform, created = Platform.objects.get_or_create(name=platform_name)

    if created and ip_address:
        msg = _('Platform [%s] registered by IP [%s].') % (
            platform_name, ip_address
        )
        models.Notification.objects.create(message=msg)

    return platform


def add_project(project_name, pms, platform, architecture, ip_address=None):
    project = Project.objects.create(
        name=project_name,
        pms=pms,
        auto_register_computers=settings.MIGASFREE_AUTOREGISTER,
        platform=platform,
        architecture=architecture
    )

    if ip_address:
        msg = _('Project [%s] with PMS [%s] registered by IP [%s].') % (
            project_name, pms, ip_address
        )
        models.Notification.objects.create(message=msg)

    return project


class PackagerKeysView(views.APIView):
    permission_classes = (permissions.IsPackager,)

    def post(self, request):
        """
        Input: {
            "username": "admin",
            "password": "admin"
        }

        Returns: {
            "migasfree-server.pub": pub_server_key,
            "migasfree-packager.pri": priv_packager_key
        }
        """
        pub_server_key_file = os.path.join(
            settings.MIGASFREE_KEYS_DIR, settings.MIGASFREE_PUBLIC_KEY
        )
        if not os.path.exists(pub_server_key_file):
            create_server_keys()

        pub_server_key = read_file(pub_server_key_file)
        priv_packager_key = read_file(os.path.join(
            settings.MIGASFREE_KEYS_DIR, settings.MIGASFREE_PACKAGER_PRI_KEY
        ))

        return Response({
            settings.MIGASFREE_PUBLIC_KEY: pub_server_key,
            settings.MIGASFREE_PACKAGER_PRI_KEY: priv_packager_key
        })


class ProjectKeysView(views.APIView):
    user = None

    def get_object(self, name, pms, platform_name, architecture, ip_address):
        try:
            return Project.objects.get(name=name)
        except Project.DoesNotExist:
            if not settings.MIGASFREE_AUTOREGISTER:
                if not self.user or not self.user.is_superuser \
                        or not self.user.has_perm('core.add_project') \
                        or not self.user.has_perm('core.add_platform'):
                    raise HttpResponseForbidden

            platform = get_platform_or_create(platform_name, ip_address)
            if not platform:
                raise HttpResponseForbidden

            project = add_project(name, pms, platform, architecture, ip_address)
            if not project:
                raise HttpResponseForbidden

            return project

    def post(self, request):
        """
        Input: {
            "user": "admin",
            "password": "admin",
            "project": "Vitalinux",
            "pms": "apt",
            "platform": "Linux",
            "architecture": "amd64 i386"
        }

        Returns: {
            "migasfree-server.pub": pub_server_key,
            "migasfree-client.pri": priv_project_key
        }
        """
        self.user = auth.authenticate(
            username=request.data.get('username'),
            password=request.data.get('password')
        )

        ip_address = get_client_ip(request)  # notifications purpose only
        project_name = request.data.get('project')
        pms = request.data.get('pms')
        platform_name = request.data.get('platform')
        architecture = request.data.get('architecture')

        # FIXME why not validate model in create method?
        available_pms = dict(get_available_pms()).keys()
        if pms not in available_pms:
            return Response(
                {'error': gettext(f'PMS must be one of {available_pms}')},
                status=status.HTTP_400_BAD_REQUEST
            )

        project = self.get_object(
            project_name, pms, platform_name, architecture, ip_address
        )

        if not settings.MIGASFREE_AUTOREGISTER and not project.auto_register_computers \
                and not self.user and not self.user.is_superuser \
                and not self.user.has_perm('client.add_computer'):
            raise HttpResponseForbidden

        priv_project_key_file = os.path.join(
            settings.MIGASFREE_KEYS_DIR, f'{project.slug}.pri'
        )
        if not os.path.exists(priv_project_key_file):
            generate_rsa_keys(project.slug)

        pub_server_key_file = os.path.join(
            settings.MIGASFREE_KEYS_DIR, settings.MIGASFREE_PUBLIC_KEY
        )
        if not os.path.exists(pub_server_key_file):
            create_server_keys()

        pub_server_key = read_file(pub_server_key_file)
        priv_project_key = read_file(priv_project_key_file)

        return Response({
            settings.MIGASFREE_PUBLIC_KEY: pub_server_key,
            'migasfree-client.pri': priv_project_key
        })


class RepositoriesKeysView(views.APIView):
    def post(self, request):
        """
        Returns the repositories public key
        """
        return Response(
            gpg_get_key('migasfree-repository'),
            content_type='text/plain'
        )
