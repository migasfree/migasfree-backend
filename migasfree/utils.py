# -*- coding: UTF-8 -*-

# Copyright (c) 2015-2019 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2019 Alberto Gacías <alberto@migasfree.org>
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
import subprocess
import fcntl
import select
import copy
import tempfile
import shutil

from datetime import timedelta
from six import iteritems
from django.conf import settings


def execute(cmd, verbose=False, interactive=False):
    """
    (int, string, string) execute(
        string cmd,
        bool verbose=False,
        bool interactive=True
    )
    """

    _output_buffer = ''

    if verbose:
        print(cmd)

    if interactive:
        _process = subprocess.Popen(
            cmd,
            shell=True,
            executable='/bin/bash'
        )
    else:
        _process = subprocess.Popen(
            cmd,
            shell=True,
            executable='/bin/bash',
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
        )

        if verbose:
            fcntl.fcntl(
                _process.stdout.fileno(),
                fcntl.F_SETFL,
                fcntl.fcntl(
                    _process.stdout.fileno(),
                    fcntl.F_GETFL
                ) | os.O_NONBLOCK,
            )

            while _process.poll() is None:
                readx = select.select([_process.stdout.fileno()], [], [])[0]
                if readx:
                    chunk = _process.stdout.read()
                    if chunk and chunk != '\n':
                        print(chunk)
                    _output_buffer = '%s%s' % (_output_buffer, chunk)

    _output, _error = _process.communicate()

    if not interactive and _output_buffer:
        _output = _output_buffer

    return _process.returncode, _output, _error


def write_file(filename, content):
    """
    bool write_file(string filename, string content)
    """

    _file = None
    try:
        _file = open(filename, 'wb')
        _file.write(content)
        _file.flush()
        os.fsync(_file.fileno())
        _file.close()

        return True
    except IOError:
        return False
    finally:
        if _file is not None:
            _file.close()


def read_file(filename):
    with open(filename, 'rb') as fp:
        ret = fp.read()

    return ret


def get_client_ip(request):
    # http://stackoverflow.com/questions/4581789/how-do-i-get-user-ip-address-in-django
    ip = request.META.get('REMOTE_ADDR')

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]

    return ip


def uuid_validate(uuid):
    if len(uuid) == 32:
        uuid = "%s-%s-%s-%s-%s" % (
            uuid[0:8],
            uuid[8:12],
            uuid[12:16],
            uuid[16:20],
            uuid[20:32]
        )

    if uuid in settings.MIGASFREE_INVALID_UUID:
        return ""
    else:
        return uuid


def uuid_change_format(uuid):
    """
    change to big-endian or little-endian format
    """
    if len(uuid) == 36:
        return "%s%s%s%s-%s%s-%s%s-%s-%s" % (
            uuid[6:8],
            uuid[4:6],
            uuid[2:4],
            uuid[0:2],
            uuid[11:13],
            uuid[9:11],
            uuid[16:18],
            uuid[14:16],
            uuid[19:23],
            uuid[24:36]
        )

    return uuid


def time_horizon(date, delay):
    """
    No weekends
    """
    weekday = int(date.strftime("%w"))  # [0(Sunday), 6]
    delta = delay + (((delay + weekday - 1) / 5) * 2)

    return date + timedelta(days=delta)


def swap_m2m(source_field, target_field):
    source_m2m = list(source_field.all())
    target_m2m = list(target_field.all())

    source_field.clear()
    source_field.add(*target_m2m)

    target_field.clear()
    target_field.add(*source_m2m)


def remove_empty_elements_from_dict(dic):
    return dict((k, v) for k, v in iteritems(dic) if v)


def remove_duplicates_preserving_order(seq):
    seen = set()
    seen_add = seen.add

    return [x for x in seq if not (x in seen or seen_add(x))]


def to_list(text):
    """
    Converts text with new lines and spaces to list (space delimiter)
    """
    return text.replace('\r', ' ').replace('\n', ' ').split() if text else []


def merge_dicts(*dicts):
    """
    Merge dictionaries with lists as values
    """
    ret = {}
    for item in dicts:
        for key in item:
            try:
                ret[key] += item[key]
            except KeyError:
                ret[key] = item[key]

    return ret


def list_difference(l1, l2):
    """ uses l1 as reference, returns list of items not in l2 """
    return list(set(l1).difference(l2))


def sort_depends(data):
    # if something fails, ask @agacias
    ret = []
    data_copy = copy.deepcopy(data)

    def sort():
        for i, s in data_copy.items():
            if not s:
                if data_copy:
                    ret.append(i)
                    del data_copy[i]
                    for _, n in data_copy.items():
                        if i in n:
                            n.remove(i)

                    sort()

        if data_copy:
            raise ValueError(data_copy)
        else:
            return ret

    return sort()


def read_remote_chunks(local_file, remote, chunk_size=8192):
    _, tmp = tempfile.mkstemp()
    with open(tmp, 'wb') as tmp_file:
        while True:
            data = remote.read(chunk_size)
            if not data:
                break
            yield data
            tmp_file.write(data)
            tmp_file.flush()

        os.fsync(tmp_file.fileno())

    shutil.move(tmp, local_file)
