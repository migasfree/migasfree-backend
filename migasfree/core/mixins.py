# Copyright (c) 2015-2025 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2025 Alberto Gacías <alberto@migasfree.org>
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
import re

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.shortcuts import get_object_or_404
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

    def verify_mtls_identity(self, request, computer_id, computer_uuid):
        """
        Verify mTLS client certificate identity if X-SSL-Client-CN header is present.

        The header format is a DN: /O=org/OU=unit/CN=UUID_CID
        (e.g., "/O=inv.org/OU=COMPUTERS/CN=201F1C33-F9DD-4197-9773-67CF86B63A5C_123")

        This verification ensures that the computer making the request matches
        the certificate's identity, preventing certificate theft/misuse.

        Args:
            request: The HTTP request object
            computer_id: The computer's database ID
            computer_uuid: The computer's UUID

        Raises:
            PermissionDenied: If the certificate identity doesn't match the request
        """
        client_dn = request.META.get('HTTP_X_SSL_CLIENT_CN')
        if not client_dn:
            # No mTLS certificate presented, skip verification
            logger.debug('No X-SSL-Client-CN header, skipping mTLS verification')
            return

        logger.debug('X-SSL-Client-CN header: %s', client_dn)

        # Parse the DN format: /O=org/OU=unit/CN=UUID_CID
        try:
            cn_match = re.search(r'/CN=([^/]+)', client_dn)
            if not cn_match:
                raise ValueError('CN not found in DN')

            cn_value = cn_match.group(1)

            # Parse the CN format: UUID_CID
            parts = cn_value.rsplit('_', 1)
            if len(parts) != 2:
                raise ValueError('Invalid CN format')

            cert_uuid, cert_cid = parts
            cert_cid = int(cert_cid)
        except (ValueError, TypeError) as e:
            logger.warning('Invalid X-SSL-Client-CN format: %s (%s)', client_dn, e)
            raise PermissionDenied(_('Invalid mTLS certificate CN format'))  # noqa: B904

        if cert_cid != computer_id:
            logger.warning('mTLS certificate CID mismatch: cert_cid=%s, computer_id=%s', cert_cid, computer_id)
            raise PermissionDenied(_('mTLS certificate does not match the requesting computer'))

        if cert_uuid.upper() != computer_uuid.upper():
            logger.warning('mTLS certificate UUID mismatch: cert_uuid=%s, computer_uuid=%s', cert_uuid, computer_uuid)
            raise PermissionDenied(_('mTLS certificate does not match the requesting computer'))

        logger.debug('mTLS identity verified: uuid=%s, cid=%s', cert_uuid, cert_cid)

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
            self.project = get_object_or_404(Project, name=data.get('project'))
            self.verify_key = f'{self.project.slug}.pub'

        claims = secure.unwrap(msg, decrypt_key=self.decrypt_key, verify_key=self.verify_key)
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

        msg = secure.wrap(data, sign_key=self.sign_key, encrypt_key=self.encrypt_key)

        return {'msg': msg}
