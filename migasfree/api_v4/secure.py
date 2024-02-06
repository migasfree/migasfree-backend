# -*- coding: utf-8 -*-

import os
import json
import subprocess

from Crypto.PublicKey import RSA
from django.conf import settings

from . import errmfs
from ..utils import read_file, write_file
from ..secure import create_server_keys

SIGN_LEN = 256


def sign(filename):
    command = [
        'openssl', 'dgst', '-sha1', '-sign', 
        os.path.join(settings.MIGASFREE_KEYS_DIR, 'migasfree-server.pri'),
        '-out', f'{filename}.sign', filename
    ]

    try:
        result = subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error signing file: {e}")


def verify(filename, key):
    # returns True if OK, False otherwise

    command = [
        'openssl', 'dgst', '-sha1', '-verify',
        os.path.join(settings.MIGASFREE_KEYS_DIR, f'{key}.pub'),
        '-signature', f'{filename}.sign',
        filename
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during verification: {e.stderr}")
        return False


def wrap(filename, data):
    """
    Creates a signed wrapper file around data
    """
    data = json.dumps(data)
    data = data.encode()
    with open(filename, 'wb') as fp:
        fp.write(data)

    sign(filename)

    with open(filename, 'ab') as fp:
        with open(f'{filename}.sign', 'rb') as fpsign:
            fp.write(fpsign.read())

    os.remove(f'{filename}.sign')


def unwrap(filename, key):
    """
    Returns data inside signed wrapper file
    """
    with open(filename, 'rb') as fp:
        content = fp.read()

    n = len(content)

    write_file(f'{filename}.sign', content[n - SIGN_LEN:n])
    write_file(filename, content[0:n - SIGN_LEN])

    if verify(filename, key):
        with open(filename, 'rb') as f:
            data = json.load(f)
    else:
        data = errmfs.error(errmfs.INVALID_SIGNATURE)

    os.remove(f'{filename}.sign')

    return data


def check_keys_path():
    if not os.path.lexists(settings.MIGASFREE_KEYS_DIR):
        os.makedirs(settings.MIGASFREE_KEYS_DIR)


def generate_rsa_keys(name='migasfree-server'):
    check_keys_path()

    private_pem = os.path.join(settings.MIGASFREE_KEYS_DIR, f'{name}.pri')
    public_pem = os.path.join(settings.MIGASFREE_KEYS_DIR, f'{name}.pub')

    if not (os.path.exists(private_pem) and os.path.exists(public_pem)):
        key = RSA.generate(2048)
        write_file(public_pem, key.publickey().exportKey('PEM'))
        write_file(private_pem, key.exportKey('PEM'))

        # read only keys
        os.chmod(private_pem, 0o400)
        os.chmod(public_pem, 0o400)


def get_keys_to_client(project):
    """
    Returns the keys for register computer
    """
    priv_project_key_file = os.path.join(
        settings.MIGASFREE_KEYS_DIR, f'{project}.pri'
    )
    if not os.path.exists(priv_project_key_file):
        generate_rsa_keys(project)

    pub_server_key_file = os.path.join(
        settings.MIGASFREE_KEYS_DIR, settings.MIGASFREE_PUBLIC_KEY
    )
    if not os.path.exists(pub_server_key_file):
        create_server_keys()

    pub_server_key = read_file(pub_server_key_file)
    priv_project_key = read_file(priv_project_key_file)

    return {
        settings.MIGASFREE_PUBLIC_KEY: pub_server_key.decode(),
        'migasfree-client.pri': priv_project_key.decode()
    }


def get_keys_to_packager():
    """
    Returns the keys for register packager
    """
    pub_server_key_file = os.path.join(
        settings.MIGASFREE_KEYS_DIR, settings.MIGASFREE_PUBLIC_KEY
    )
    if not os.path.exists(pub_server_key_file):
        create_server_keys()

    pub_server_key = read_file(pub_server_key_file)
    priv_packager_key = read_file(
        os.path.join(
            settings.MIGASFREE_KEYS_DIR,
            settings.MIGASFREE_PACKAGER_PRI_KEY
        )
    )

    return {
        settings.MIGASFREE_PUBLIC_KEY: pub_server_key.decode(),
        settings.MIGASFREE_PACKAGER_PRI_KEY: priv_packager_key.decode()
    }
