# -*- coding: utf-8 -*-

# Copyright (c) 2015-2018 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2018 Alberto Gacías <alberto@migasfree.org>
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
import gpgme
import json

from io import BytesIO
from jwcrypto import jwk, jwe, jws
from jwcrypto.common import json_encode
from django.conf import settings

from .utils import read_file, write_file


def sign(claims, priv_key):
    """
    string sign(dict claims, string priv_key)
    """
    priv_jwk = jwk.JWK.from_pem(
        read_file(os.path.join(settings.MIGASFREE_KEYS_DIR, priv_key))
    )

    if isinstance(claims, dict):
        claims = json.dumps(claims)

    jws_token = jws.JWS(str(claims))
    jws_token.add_signature(
        priv_jwk,
        header=json_encode({'alg': 'RS256', "kid": priv_jwk.thumbprint()})
    )

    return jws_token.serialize()


def verify(jwt, pub_key):
    """
    dict verify(string jwt, string pub_key)
    """
    pub_jwk = jwk.JWK.from_pem(
        read_file(os.path.join(settings.MIGASFREE_KEYS_DIR, pub_key))
    )

    jws_token = jws.JWS()
    jws_token.deserialize(jwt)
    jws_token.verify(pub_jwk)

    return jws_token.payload


def encrypt(claims, pub_key):
    """
    string encrypt(dict claims, string pub_key)
    """
    pub_jwk = jwk.JWK.from_pem(
        read_file(os.path.join(settings.MIGASFREE_KEYS_DIR, pub_key))
    )

    protected_header = {
        "alg": "RSA-OAEP-256",
        "enc": "A256CBC-HS512",
        "typ": "JWE",
        "kid": pub_jwk.thumbprint(),
    }
    jwe_token = jwe.JWE(
        json.dumps(claims),
        recipient=pub_jwk,
        protected=protected_header
    )
    jwt = jwe_token.serialize()

    return jwt


def decrypt(jwt, priv_key):
    """
    string decrypt(string jwt, string priv_key)
    """
    priv_jwk = jwk.JWK.from_pem(
        read_file(os.path.join(settings.MIGASFREE_KEYS_DIR, priv_key))
    )

    jwe_token = jwe.JWE()
    jwe_token.deserialize(jwt, key=priv_jwk)

    return jwe_token.payload


def wrap(data, sign_key, encrypt_key):
    claims = {
        'data': data,
        'sign': sign(data, sign_key)
    }
    return encrypt(claims, encrypt_key)


def unwrap(data, decrypt_key, verify_key):
    jwt = json.loads(decrypt(data, decrypt_key))
    jws = verify(jwt['sign'], verify_key)
    if jws:
        return jwt['data']

    return None


def check_keys_path():
    if not os.path.lexists(settings.MIGASFREE_KEYS_DIR):
        os.makedirs(settings.MIGASFREE_KEYS_DIR)


def generate_rsa_keys(name='migasfree-server'):
    check_keys_path()

    private_pem = os.path.join(settings.MIGASFREE_KEYS_DIR, '{}.pri'.format(name))
    public_pem = os.path.join(settings.MIGASFREE_KEYS_DIR, '{}.pub'.format(name))

    key = jwk.JWK.generate(kty='RSA', size=2048)
    write_file(public_pem, key.export_to_pem())
    write_file(private_pem, key.export_to_pem(private_key=True, password=None))

    # read only keys
    os.chmod(private_pem, 0o400)
    os.chmod(public_pem, 0o400)


def create_server_keys():
    generate_rsa_keys("migasfree-server")
    generate_rsa_keys("migasfree-packager")
    gpg_get_key("migasfree-repository")


def gpg_get_key(name):
    """
    Returns GPG keys (if not exists it is created)
    """

    gpg_home = os.path.join(settings.MIGASFREE_KEYS_DIR, '.gnupg')
    gpg_conf = os.path.join(gpg_home, 'gpg.conf')
    gpg_agent_conf = os.path.join(gpg_home, 'gpg-agent.conf')
    _file = os.path.join(gpg_home, '{}.gpg'.format(name))

    if not os.path.exists(_file):
        os.environ['GNUPGHOME'] = gpg_home
        if not os.path.exists(gpg_home):
            os.makedirs(gpg_home, 0o700)
            # creates configuration file
            write_file(gpg_conf, 'cert-digest-algo SHA256\ndigest-algo SHA256\nuse-agent\npinentry-mode loopback')
            os.chmod(gpg_conf, 0o600)
            write_file(gpg_agent_conf, 'allow-loopback-pinentry')
            os.chmod(gpg_agent_conf, 0o600)

        key_params = """
Key-Type: RSA
Key-Length: 4096
Name-Real: %s
Name-Email: fun.with@migasfree.org
Expire-Date: 0
"""
        file_params = os.path.join(gpg_home, '{}.txt'.format(name))
        write_file(file_params, key_params % name)

        os.system(
            "echo '' | $(which gpg) --batch "
            "--passphrase-fd 0 --gen-key %(file)s; rm %(file)s" % {
                "file": file_params
            }
        )

        # export and save
        ctx = gpgme.Context()
        ctx.armor = True
        key_data = BytesIO()
        ctx.export(name, key_data)
        write_file(_file, key_data.getvalue())
        os.chmod(_file, 0o600)

    return read_file(_file)
