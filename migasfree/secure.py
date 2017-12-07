# -*- coding: utf-8 -*-

# Copyright (c) 2015-2017 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2017 Alberto Gacías <alberto@migasfree.org>
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
import jose
import gpgme

from io import BytesIO
from Crypto.PublicKey import RSA
from django.conf import settings

from .utils import read_file, write_file


def sign(claims, priv_key):
    rsa_key = RSA.importKey(
        read_file(os.path.join(settings.MIGASFREE_KEYS_DIR, priv_key))
    )
    jwk = {'k': rsa_key.exportKey('PEM')}

    jws = jose.sign(claims, jwk, alg='RS256')  # Asymmetric!!!
    jwt = jose.serialize_compact(jws)

    return jwt


def verify(jwt, pub_key):
    rsa_key = RSA.importKey(
        read_file(os.path.join(settings.MIGASFREE_KEYS_DIR, pub_key))
    )
    jwk = {'k': rsa_key.exportKey('PEM')}
    try:
        jwe = jose.deserialize_compact(jwt)
        return jose.verify(jwe, jwk, alg='RS256')  # Asymmetric!!!
    except:
        # DEBUG
        import sys
        import traceback
        traceback.print_exc(file=sys.stdout)
        return None


def encrypt(claims, pub_key):
    rsa_key = RSA.importKey(
        read_file(os.path.join(settings.MIGASFREE_KEYS_DIR, pub_key))
    )
    pub_jwk = {'k': rsa_key.publickey().exportKey('PEM')}

    jwe = jose.encrypt(claims, pub_jwk)
    jwt = jose.serialize_compact(jwe)

    return jwt


def decrypt(jwt, priv_key):
    rsa_key = RSA.importKey(
        read_file(os.path.join(settings.MIGASFREE_KEYS_DIR, priv_key))
    )
    priv_jwk = {'k': rsa_key.exportKey('PEM')}
    try:
        jwe = jose.deserialize_compact(jwt)
        return jose.decrypt(jwe, priv_jwk)
    except:
        return None


def wrap(data, sign_key, encrypt_key):
    claims = {
        'data': data,
        'sign': sign(data, sign_key)
    }
    return encrypt(claims, encrypt_key)


def unwrap(data, decrypt_key, verify_key):
    jwt = decrypt(data, decrypt_key)
    jws = verify(jwt.claims['sign'], verify_key)
    if jws:
        return jwt.claims['data']

    return None


def check_keys_path():
    if not os.path.lexists(settings.MIGASFREE_KEYS_DIR):
        os.makedirs(settings.MIGASFREE_KEYS_DIR)


def generate_rsa_keys(name='migasfree-server'):
    check_keys_path()

    private_pem = os.path.join(settings.MIGASFREE_KEYS_DIR, '{}.pri'.format(name))
    public_pem = os.path.join(settings.MIGASFREE_KEYS_DIR, '{}.pub'.format(name))

    key = RSA.generate(2048)
    write_file(public_pem, key.publickey().exportKey('PEM'))
    write_file(private_pem, key.exportKey('PEM'))

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
    _file = os.path.join(gpg_home, '{}.gpg'.format(name))

    if not os.path.exists(_file):
        os.environ['GNUPGHOME'] = gpg_home
        if not os.path.exists(gpg_home):
            os.makedirs(gpg_home, 0o700)
            # creates configuration file
            write_file(gpg_conf, 'cert-digest-algo SHA256\ndigest-algo SHA256')
            os.chmod(gpg_conf, 0o600)

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
