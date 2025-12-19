import json
import logging
import os

from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt

from ...client.models import Error, Notification
from ...utils import get_client_ip, read_file, uuid_validate
from .. import errmfs
from ..api import (
    create_repositories_of_packageset,
    get_computer,
    get_computer_software,
    get_computer_tags,
    get_key_packager,
    get_properties,
    register_computer,
    return_message,
    save_request_file,
    set_computer_tags,
    upload_computer_errors,
    upload_computer_faults,
    upload_computer_hardware,
    upload_computer_info,
    upload_computer_message,
    upload_computer_software_base,
    upload_computer_software_base_diff,
    upload_computer_software_history,
    upload_devices_changes,
    upload_server_package,
    upload_server_set,
)
from ..secure import unwrap, wrap

logger = logging.getLogger('migasfree')

# USING USERNAME AND PASSWORD ONLY (WITHOUT KEYS PAIR)
API_REGISTER = {
    'register_computer': register_computer,
    'get_key_packager': get_key_packager,
}

# USING "PACKAGER" KEYS PAIR
API_PACKAGER = {
    'upload_server_package': upload_server_package,
    'upload_server_set': upload_server_set,
    'create_repositories_of_packageset': create_repositories_of_packageset,
}

# USING "PROJECT" KEYS
API_PROJECT = {
    'upload_computer_message': upload_computer_message,
    'get_properties': get_properties,
    'upload_computer_info': upload_computer_info,
    'upload_computer_faults': upload_computer_faults,
    'upload_computer_hardware': upload_computer_hardware,
    'upload_computer_software_base_diff': upload_computer_software_base_diff,
    'upload_computer_software_base': upload_computer_software_base,
    'upload_computer_software_history': upload_computer_software_history,
    'get_computer_software': get_computer_software,
    'upload_computer_errors': upload_computer_errors,
    'upload_devices_changes': upload_devices_changes,
    'set_computer_tags': set_computer_tags,
    'get_computer_tags': get_computer_tags,
}


def check_tmp_path():
    if not os.path.exists(settings.MIGASFREE_TMP_DIR):
        try:
            os.makedirs(settings.MIGASFREE_TMP_DIR, 0o700)
        except OSError:
            return False

    return True


def wrap_command_result(filename, result):
    wrap(filename, result)
    ret = read_file(filename)
    os.remove(filename)

    return ret


def get_msg_info(text):
    slices = text.split('.')
    if len(slices) == 2:  # COMPATIBILITY WITHOUT UUID
        name, command = slices
        uuid = name
    else:  # WITH UUID
        name = '.'.join(slices[:-2])
        uuid = uuid_validate(slices[-2]) or name
        command = slices[-1]

    return command, uuid, name


@csrf_exempt
def api_v4(request):
    if not check_tmp_path():
        return HttpResponse(
            return_message('temporal_path_not_created', errmfs.error(errmfs.GENERIC)), content_type='text/plain'
        )

    if request.method != 'POST':
        return HttpResponse(
            return_message('unexpected_get_method', errmfs.error(errmfs.GET_METHOD_NOT_ALLOWED)),
            content_type='text/plain',
        )

    msg = request.FILES.get('message')
    if not msg:
        return HttpResponse(return_message('no_message_file', errmfs.error(errmfs.GENERIC)), content_type='text/plain')

    filename = os.path.normpath(os.path.join(settings.MIGASFREE_TMP_DIR, msg.name))
    if not filename.startswith(settings.MIGASFREE_TMP_DIR):
        return HttpResponse(
            return_message('invalid_file_path', errmfs.error(errmfs.GENERIC)), content_type='text/plain'
        )

    filename_return = f'{filename}.return'

    command, uuid, name = get_msg_info(msg.name)
    computer = get_computer(name, uuid)

    if computer and computer.status == 'unsubscribed':
        Error.objects.create(
            computer,
            computer.project,
            f'{get_client_ip(request)} - {command} - {errmfs.error_info(errmfs.UNSUBSCRIBED_COMPUTER)}',
        )
        ret = return_message(command, errmfs.error(errmfs.UNSUBSCRIBED_COMPUTER))
        return HttpResponse(wrap_command_result(filename_return, ret), content_type='text/plain')

    if computer and computer.status == 'available' and command == 'upload_computer_info':
        Notification.objects.create(_('Computer [%s] with available status, has been synchronized') % computer)

    # COMPUTERS
    if command in API_PROJECT:  # IF COMMAND IS BY PROJECT
        if computer:
            save_request_file(msg, filename)

            data = unwrap(filename, computer.project.name)
            if 'errmfs' in data:
                ret = return_message(command, data)

                if data['errmfs']['code'] == errmfs.INVALID_SIGNATURE:
                    Error.objects.create(
                        computer,
                        computer.project,
                        f'{get_client_ip(request)} - {command} - {errmfs.error_info(errmfs.INVALID_SIGNATURE)}',
                    )
            else:
                handler = API_PROJECT.get(command)
                if handler:
                    ret = handler(request, name, uuid, computer, data)
                else:
                    ret = return_message(command, errmfs.error(errmfs.COMMAND_NOT_FOUND))

            os.remove(filename)
        else:
            ret = return_message(command, errmfs.error(errmfs.COMPUTER_NOT_FOUND))

        return HttpResponse(wrap_command_result(filename_return, ret), content_type='text/plain')

    # REGISTERS
    # COMMAND NOT USE KEYS PAIR, ONLY USERNAME AND PASSWORD
    elif command in API_REGISTER:
        save_request_file(msg, filename)

        with open(filename, 'rb') as f:
            data = json.load(f)[command]

        try:
            handler = API_REGISTER.get(command)
            if handler:
                ret = handler(request, name, uuid, computer, data)
            else:
                ret = return_message(command, errmfs.error(errmfs.COMMAND_NOT_FOUND))
        except Exception as e:
            logger.error('Error in register API command %s: %s', command, e)
            ret = return_message(command, errmfs.error(errmfs.GENERIC))

        os.remove(filename)

        return HttpResponse(json.dumps(ret), content_type='text/plain')

    # PACKAGER
    elif command in API_PACKAGER:
        save_request_file(msg, filename)

        data = unwrap(filename, 'migasfree-packager')
        if 'errmfs' in data:
            ret = data
        else:
            handler = API_PACKAGER.get(command)
            if handler:
                ret = handler(request, name, uuid, computer, data[command])
            else:
                ret = return_message(command, errmfs.error(errmfs.COMMAND_NOT_FOUND))

        os.remove(filename)

        return HttpResponse(wrap_command_result(filename_return, ret), content_type='text/plain')

    else:
        return HttpResponse(return_message(command, errmfs.error(errmfs.COMMAND_NOT_FOUND)), content_type='text/plain')
