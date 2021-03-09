import json

from django.conf import settings
from django.http import HttpResponse, JsonResponse, Http404
from django.template import Context, Template

from ...utils import uuid_validate
from .client_api import get_computer


LABEL_TEMPLATE = """
<html>
    <head>
        <title>{{ search }}</title>
        <style type="text/css">
        body {
            width: 35em;
            height: 10em;
            border: 1px solid #000;
            padding: .5em 1em;
        }
        h2 {
            font-size: 100%;
        }
        h3 {
            text-align: center;
        }
        p {
            border-top: 1px solid #000;
            text-align: center;
        }
        </style>
    </head>
    <body>
        <h1>{{ search }}</h1>
        <h2>{{ uuid }}</h2>
        <h3>Server: {{ server }}</h3>
        <p>{{ helpdesk }}</p>
    </body>
</html>
"""


def get_computer_info(request, uuid=None):
    if uuid:
        _uuid = uuid_validate(uuid)
    else:
        _uuid = uuid_validate(request.GET.get('uuid', ''))
    _name = request.GET.get('name', '')
    if _uuid == "":
        _uuid = _name

    computer = get_computer(_name, _uuid)
    if not computer:
        raise Http404

    result = {
        'id': computer.id,
        'uuid': computer.uuid,
        'name': computer.__str__(),
        'helpdesk': settings.MIGASFREE_HELP_DESK,
        'server': request.META.get('HTTP_HOST'),
        'tags': ["{}-{}".format(tag.property_att.prefix, tag.value) for tag in computer.tags.all()],
        'available_tags': {},
    }
    result['search'] = result[settings.MIGASFREE_COMPUTER_SEARCH_FIELDS[0]]

    return JsonResponse(result)


def computer_label(request, uuid=None):
    """
    To Print a Computer Label
    """
    if not uuid:
        uuid = request.GET.get('uuid', '')

    computer_info = json.loads(get_computer_info(request, uuid).content)

    template = Template(LABEL_TEMPLATE)
    context = Context(computer_info)

    return HttpResponse(template.render(context))