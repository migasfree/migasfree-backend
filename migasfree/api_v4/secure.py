# -*- coding: utf-8 -*-

import os
import re
import json
import subprocess

from django.conf import settings

from . import errmfs
from ..utils import read_file, write_file
from ..secure import create_server_keys, generate_rsa_keys

SIGN_LEN = 256


def is_safe_filename(filename):
    # Allow only alphanumeric characters, dashes, and underscores in filenames
    if re.match(r'^[\w\-. ]+$', filename) is None:
        return False

    # Check for any dangerous patterns or reserved filenames
    dangerous_patterns = ['..', '/', '\\', '|', ';', '&', '$', '>', '<']
    for pattern in dangerous_patterns:
        if pattern in filename:
            return False

    return True


def sign(filename):
    if not is_safe_filename(filename):
        print(f"Invalid filename: {filename}")
        return False

    command = [
        'openssl', 'dgst', '-sha1', '-sign',
        os.path.join(settings.MIGASFREE_KEYS_DIR, 'migasfree-server.pri'),
        '-out', f'{filename}.sign', filename
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error signing file: {e}")


def verify(filename, key):
    # returns True if OK, False otherwise

    if not is_safe_filename(filename):
        print(f"Invalid filename: {filename}")
        return False

    command = [
        'openssl', 'dgst', '-sha1', '-verify',
        os.path.join(settings.MIGASFREE_KEYS_DIR, f'{key}.pub'),
        '-signature', f'{filename}.sign',
        filename
    ]

    try:
        subprocess.run(command, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during verification: {e.stderr}")
        return False


def wrap(filename, data):
    """
    Creates a signed wrapper file around data
    """

    if not is_safe_filename(filename):
        print(f"Invalid filename: {filename}")
        return False

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

    if not is_safe_filename(filename):
        print(f"Invalid filename: {filename}")
        return False

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
