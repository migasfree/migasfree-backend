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

import copy
import fcntl
import hashlib
import json
import os
import select
import subprocess
import tempfile
from datetime import timedelta


def get_setting(name):
    ret = os.environ.get(name, None)
    if not ret:
        try:
            from django.conf import settings

            ret = getattr(settings, name, None)
        except (ImportError, AttributeError):
            pass

    return ret


def get_secret(name):
    file_ = os.path.join(get_setting('MIGASFREE_SECRET_DIR'), name)
    if os.path.exists(file_):
        return read_file(file_).decode().strip()

    return ''


def cmp(a, b):
    return (a > b) - (a < b)


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
        _process = subprocess.Popen(cmd, shell=True, executable='/bin/bash')
    else:
        _process = subprocess.Popen(
            cmd, shell=True, executable='/bin/bash', stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )

        if verbose:
            fcntl.fcntl(
                _process.stdout.fileno(),
                fcntl.F_SETFL,
                fcntl.fcntl(_process.stdout.fileno(), fcntl.F_GETFL) | os.O_NONBLOCK,
            )

            while _process.poll() is None:
                readx = select.select([_process.stdout.fileno()], [], [])[0]
                if readx:
                    chunk = _process.stdout.read()
                    if chunk and chunk != '\n':
                        print(chunk)
                    _output_buffer = f'{_output_buffer}{chunk}'

    _output, _error = _process.communicate()

    if not interactive and _output_buffer:
        _output = _output_buffer

    if isinstance(_output, bytes) and not isinstance(_output, str):
        _output = str(_output, encoding='utf8')
    if isinstance(_error, bytes) and not isinstance(_error, str):
        _error = str(_error, encoding='utf8')

    return _process.returncode, _output, _error


def write_file(filename, content):
    """
    bool write_file(string filename, string content)
    """

    try:
        with open(filename, 'wb') as file:
            try:
                file.write(content.encode('utf-8'))
            except AttributeError:
                file.write(content)

            file.flush()
            os.fsync(file.fileno())

        return True
    except OSError:
        return False


def read_file(filename):
    with open(filename, 'rb') as _file:
        ret = _file.read()

    return ret


def get_client_ip(request):
    if not hasattr(request, 'META') or not isinstance(request.META, dict):
        return None

    # http://stackoverflow.com/questions/4581789/how-do-i-get-user-ip-address-in-django
    ip = request.META.get('REMOTE_ADDR')

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()

    return ip


def get_proxied_ip_address(request):
    ip = request.META.get('REMOTE_ADDR')
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        forwarded_ip = x_forwarded_for.split(',')[0].strip()
        if ip != forwarded_ip:
            ip = f'{ip}/{forwarded_ip}'

    return ip


def uuid_validate(uuid):
    if len(uuid) == 32:
        uuid = f'{uuid[0:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:32]}'

    if uuid in get_setting('MIGASFREE_INVALID_UUID'):
        return ''

    return uuid


def uuid_change_format(uuid):
    """
    change to big-endian or little-endian format
    """
    if not uuid:
        return ''

    if len(uuid) == 36:
        return f'{uuid[6:8]}{uuid[4:6]}{uuid[2:4]}{uuid[0:2]}-{uuid[11:13]}{uuid[9:11]}-{uuid[16:18]}{uuid[14:16]}-{uuid[19:23]}-{uuid[24:36]}'

    return uuid


def time_horizon(date, delay):
    """
    No weekends
    """
    weekday = date.weekday()  # [0 (Monday), 6 (Sunday)]
    delta = delay + ((delay + weekday) // 5 * 2)

    return date + timedelta(days=delta)


def swap_m2m(source, target, field):
    source_m2m = list(getattr(source, field).values_list('pk', flat=True))
    target_m2m = list(getattr(target, field).values_list('pk', flat=True))

    getattr(source, field).set(target_m2m)
    getattr(target, field).set(source_m2m)


def remove_empty_elements_from_dict(dic):
    return {k: remove_empty_elements_from_dict(v) if isinstance(v, dict) else v for k, v in dic.items() if v and k}


def replace_keys(data, aliases):
    return [{aliases.get(key, key): value for key, value in item.items()} for item in data]


def remove_duplicates_preserving_order(seq):
    """
    Removes duplicates from a sequence while preserving the original order of the elements.

    Args:
        seq (list): A sequence of elements.

    Returns:
        list: A new list with the duplicates removed while preserving the original order of the elements.
    """
    seen = set()
    seen_add = seen.add

    return [x for x in seq if not (x in seen or seen_add(x))]


def escape_format_string(text):
    return text.replace('{', '{{').replace('}', '}}')


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
    for dictionary in dicts:
        for key, value in dictionary.items():
            if key in ret and isinstance(ret[key], list):
                ret[key].extend(value)
            else:
                ret[key] = value

    return ret


def list_difference(l1, l2):
    """uses l1 as reference, returns list of items not in l2"""
    return list(set(l1).difference(l2))


def list_common(l1, l2):
    """uses l1 as reference, returns list of items in l2 (api_v4)"""
    return list(set(l1).intersection(l2))


def sort_depends(data):
    # if something fails, ask @agacias
    ret = []
    data_copy = copy.deepcopy(data)

    def sort():
        for item, dependencies in list(data_copy.items()):
            if not dependencies and data_copy:
                ret.append(item)
                del data_copy[item]
                for _, other_dependencies in list(data_copy.items()):
                    if item in other_dependencies:
                        other_dependencies.remove(item)

                sort()

        if data_copy:
            raise ValueError('Circular dependencies detected.', data_copy)

        return ret

    return sort()


def save_tempfile(file_):
    # prefix must ends always in slash
    prefix = os.path.join(get_setting('MIGASFREE_TMP_DIR'), '')
    _, tempfn = tempfile.mkstemp(prefix=prefix)
    try:
        with open(tempfn, 'wb') as temp_file:
            for chunk in file_.chunks():
                temp_file.write(chunk)
    except OSError:
        raise Exception(f'Problem with the input file {file_.name}')  # noqa: B904

    return tempfn


def decode_dict(value):
    """
    https://www.geeksforgeeks.org/python-convert-bytestring-keyvalue-pair-of-dictionary-to-string/
    """
    return {y.decode(): value.get(y).decode() for y in value}


def decode_set(value):
    return {i.decode() for i in value}


def to_heatmap(results, range_name='day'):
    """
    :param results: [{"day": datetime, "count": int}, ...]
    :param range_name
    :return: [["YYYY-MM-DD", int], ...]
    """

    return [[item[range_name].strftime('%Y-%m-%d'), item['count']] for item in results]


def hash_args(args, kwargs):
    return hashlib.md5(json.dumps((args, kwargs)).encode()).hexdigest()


def normalize_line_breaks(text):
    return text.replace('\r\n', '\n') if text else text
