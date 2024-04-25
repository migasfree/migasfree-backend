# -*- coding: UTF-8 -*-

import os
import sys
import traceback
import tempfile

from django.conf import settings
from django.template import Context, Template
from django.utils.translation import gettext as _


ALL_OK = 0
UNAUTHENTICATED = 1
CAN_NOT_REGISTER_COMPUTER = 2
GET_METHOD_NOT_ALLOWED = 3
COMMAND_NOT_FOUND = 4
INVALID_SIGNATURE = 5
COMPUTER_NOT_FOUND = 6
DEVICE_NOT_FOUND = 7
PROJECT_NOT_FOUND = 8
USER_DOES_NOT_HAVE_PERMISSION = 9
UNSUBSCRIBED_COMPUTER = 10
GENERIC = 100

ERROR_INFO = {
    ALL_OK: _("No errors"),
    UNAUTHENTICATED: _("User unauthenticated"),
    CAN_NOT_REGISTER_COMPUTER: _("User can not register computers"),
    GET_METHOD_NOT_ALLOWED: _("Method GET not allowed"),
    COMMAND_NOT_FOUND: _("Command not found"),
    INVALID_SIGNATURE: _("Signature is not valid"),
    COMPUTER_NOT_FOUND: _("Computer not found"),
    DEVICE_NOT_FOUND: _("Device not found"),
    PROJECT_NOT_FOUND: _("Project not found"),
    USER_DOES_NOT_HAVE_PERMISSION: _("User does not have permission"),
    UNSUBSCRIBED_COMPUTER: _("Unsubscribed computer"),
    GENERIC: _("Generic error")
}

ERROR_TEMPLATE = """
<html>
<head>
    <title>{{ description }}</title>
</head>
<body>
    <h1>{{ description }}</h1>

    {% for row in traceback %}
        <p>
            <strong>
                File: {{ row.filename }}
                <br />Name: {{ row.name }}
                <br />Line: {{ row.line }}
            </strong>
        </p>
        {% for variable in row.locals %}
            <pre>{{ variable.key }}={{ variable.value }}</pre>
        {% endfor %}
    {% endfor %}
</body>
</html>
"""


def error_info(number):
    """
    string error_info(int number)
    """
    return ERROR_INFO.get(number, '')


def error(number):
    ret = error_info(number)
    if settings.DEBUG and number == GENERIC:
        etype = sys.exc_info()[0]
        evalue = sys.exc_info()[1]

        dir_errors = os.path.join(settings.MIGASFREE_PUBLIC_DIR, '.errors')
        if not os.path.exists(dir_errors):
            os.makedirs(dir_errors)

        with tempfile.NamedTemporaryFile(
            mode='w+b',
            suffix='.html',
            prefix=str(evalue).replace(" ", "_").replace("\n", "_"),
            dir=dir_errors,
            delete=False
        ) as fp:
            fp.write(print_exc_plus(etype, evalue))
            fp_name = os.path.join(dir_errors, os.path.basename(fp.name))

        ret = f'{etype} {evalue} {_("Traceback")}: {fp_name}'

    return {"errmfs": {"code": number, "info": ret}}


def ok():
    return error(ALL_OK)


def print_exc_plus(etype, evalue):
    """
    Print the usual traceback information, followed by a listing of all the
    local variables in each frame.
    """
    tb = sys.exc_info()[2]
    while 1:
        if not tb.tb_next:
            break
        tb = tb.tb_next

    stack = []
    f = tb.tb_frame
    while f:
        stack.append(f)
        f = f.f_back

    stack.reverse()
    traceback.print_exc()

    ret = []
    for frame in stack:
        fr = {
            'filename': frame.f_code.co_filename,
            'name': frame.f_code.co_name,
            'line': frame.f_lineno
        }

        variables = []
        for key, value in frame.f_locals.items():
            try:
                variables.append({"key": key, "value": str(value)})
            except Exception:
                pass

        fr["locals"] = variables
        ret.append(fr)

    template = Template(ERROR_TEMPLATE)
    context = Context({
        "description": '%s: %s %s' % (
            _("Generic error in server"),
            str(etype),
            str(evalue)
        ),
        "traceback": ret
    })

    return template.render(context)
