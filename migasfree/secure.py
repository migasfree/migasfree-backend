# -*- coding: utf-8 -*-

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

import os
import json
import subprocess
import logging

from jwcrypto import jwk, jwe, jws
from jwcrypto.common import json_encode
from django.conf import settings
from django.utils.translation import gettext

from migasfree import __contact__
from .utils import read_file, write_file

logger = logging.getLogger('migasfree')


def load_jwk(filename):
    """
    Loads a JWK from a PEM file

    Args:
        filename (str)

    Returns:
        jwk.JWK: loaded JWK object
    """
    return jwk.JWK.from_pem(
        read_file(os.path.join(settings.MIGASFREE_KEYS_DIR, filename))
    )


def sign(claims, priv_key):
    """
    string sign(dict claims, string priv_key)
    """
    if isinstance(claims, dict):
        claims = json.dumps(claims)

    priv_jwk = load_jwk(priv_key)
    jws_token = jws.JWS(str(claims))
    jws_token.add_signature(
        priv_jwk,
        header=json_encode({
            'alg': 'RS256',
            'kid': priv_jwk.thumbprint()
        })
    )

    return jws_token.serialize()


def verify(jwt, pub_key):
    """
    dict verify(string jwt, string pub_key)
    """
    jws_token = jws.JWS()
    jws_token.deserialize(jwt)
    jws_token.verify(load_jwk(pub_key))

    return jws_token.payload


def encrypt(claims, pub_key):
    """
    string encrypt(dict claims, string pub_key)
    """
    pub_jwk = load_jwk(pub_key)

    protected_header = {
        'alg': 'RSA-OAEP-256',
        'enc': 'A256CBC-HS512',
        'typ': 'JWE',
        'kid': pub_jwk.thumbprint(),
    }
    jwe_token = jwe.JWE(
        json.dumps(claims),
        recipient=pub_jwk,
        protected=protected_header
    )

    return jwe_token.serialize()


def decrypt(jwt, priv_key):
    """
    string decrypt(string jwt, string priv_key)
    """
    jwe_token = jwe.JWE()
    jwe_token.deserialize(jwt, key=load_jwk(priv_key))

    if isinstance(jwe_token.payload, bytes) \
            and not isinstance(jwe_token.payload, str):
        return str(jwe_token.payload, encoding='utf8')

    return jwe_token.payload


def wrap(data, sign_key, encrypt_key):
    """
    string wrap(dict data, string sign_key, string encrypt_key)
    """
    claims = {
        'data': data,
        'sign': sign(data, sign_key)
    }

    return encrypt(claims, encrypt_key)


def unwrap(data, decrypt_key, verify_key):
    """
    dict unwrap(string data, string decrypt_key, string verify_key)
    """
    try:
        jwt = json.loads(decrypt(data, decrypt_key))
    except jwe.InvalidJWEData as e:
        logger.debug('exception: %s', str(e))
        logger.debug('data: %s', data)
        logger.debug('decrypt key: %s', decrypt_key)
        return gettext('Invalid Data')

    try:
        jws_payload = verify(jwt['sign'], verify_key)
    except jws.InvalidJWSSignature as e:
        logger.debug('exception: %s', str(e))
        logger.debug('sign: %s', jwt['sign'])
        logger.debug('verify key: %s', verify_key)
        return gettext('Invalid Signature')

    if jws_payload:
        return jwt['data']

    return None


def check_keys_path():
    if not os.path.lexists(settings.MIGASFREE_KEYS_DIR):
        os.makedirs(settings.MIGASFREE_KEYS_DIR)


def generate_rsa_keys(name='migasfree-server'):
    check_keys_path()

    private_pem = os.path.join(settings.MIGASFREE_KEYS_DIR, f'{name}.pri')
    public_pem = os.path.join(settings.MIGASFREE_KEYS_DIR, f'{name}.pub')

    key = jwk.JWK.generate(kty='RSA', size=2048)
    write_file(public_pem, key.export_to_pem())
    write_file(private_pem, key.export_to_pem(private_key=True, password=None))

    # read only keys
    os.chmod(private_pem, 0o400)
    os.chmod(public_pem, 0o400)


def create_server_keys():
    generate_rsa_keys('migasfree-server')
    generate_rsa_keys('migasfree-packager')
    gpg_get_key('migasfree-repository')


def gpg_get_key(name):
    """
    Returns GPG keys (if not exists it is created)
    """

    gpg_home = os.path.join(settings.MIGASFREE_KEYS_DIR, '.gnupg')
    gpg_conf = os.path.join(gpg_home, 'gpg.conf')
    gpg_agent_conf = os.path.join(gpg_home, 'gpg-agent.conf')
    public_key = os.path.join(gpg_home, f'{name}.gpg')
    private_key = os.path.join(gpg_home, f'{name}.sec')

    if not os.path.exists(gpg_home):
        os.makedirs(gpg_home, 0o700)
        # creates configuration file
        write_file(
            gpg_conf,
            'cert-digest-algo SHA256\ndigest-algo SHA256\nuse-agent\npinentry-mode loopback'
        )
        os.chmod(gpg_conf, 0o600)
        write_file(gpg_agent_conf, 'allow-loopback-pinentry')
        os.chmod(gpg_agent_conf, 0o600)

    if not os.path.exists(public_key):
        os.environ['GNUPGHOME'] = gpg_home

        key_params = f"""
Key-Type: RSA
Key-Length: 4096
Name-Real: {name}
Name-Email: {__contact__}
Expire-Date: 0
"""

        command = [
            'gpg', '--batch', '--generate-key',
            '--pinentry-mode', 'loopback', '--passphrase', ''
        ]
        subprocess.run(command, input=key_params, text=True, capture_output=True)

        # export and save public key
        command = ['gpg', '--list-keys', f'{name}']
        output = subprocess.check_output(command, text=True)
        fingerprint = output.split('\n')[1].split('/')[-1].strip()

        command = ['gpg', '--armor', '--export', fingerprint, '>', public_key]
        subprocess.check_call(' '.join(command), shell=True)
        os.chmod(public_key, 0o600)

        # export and save private key
        command = ['gpg', '--armor', '--export-secret-key', fingerprint, '>', private_key]
        subprocess.check_call(' '.join(command), shell=True)
        os.chmod(private_key, 0o600)

    return read_file(public_key)
