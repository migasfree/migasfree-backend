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

import logging

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from .. import secure
from .models import Project

logger = logging.getLogger('migasfree')


class SafeConnectionMixin:
    project = None
    decrypt_key = settings.MIGASFREE_PRIVATE_KEY
    sign_key = settings.MIGASFREE_PRIVATE_KEY

    verify_key = None
    encrypt_key = None

    def get_claims(self, data):
        """
        Decrypt and verify data
        data = {
            'msg': jwt,
            'project': project_name
        }
        """
        msg = data.get('msg')
        if not self.verify_key:
            self.project = get_object_or_404(
                Project, name=data.get('project')
            )
            self.verify_key = f'{self.project.slug}.pub'
        claims = secure.unwrap(
            msg,
            decrypt_key=self.decrypt_key,
            verify_key=self.verify_key
        )
        logger.debug('get_claims: %s', claims)
        return claims

    def create_response(self, data):
        """
        Sign and encrypt data
        Returns: {
            'msg': jwt
        }
        """
        if not self.project and not self.encrypt_key:
            raise ObjectDoesNotExist(_('No key to sign message'))

        logger.debug('create_response: %s', data)
        if not self.encrypt_key:
            self.encrypt_key = f'{self.project.slug}.pub'

        msg = secure.wrap(
            data,
            sign_key=self.sign_key,
            encrypt_key=self.encrypt_key
        )

        return {'msg': msg}
