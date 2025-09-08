import json

from django.conf import settings
from django.http import HttpResponse, JsonResponse, Http404
from django.template import Context, Template
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiTypes
from rest_framework.decorators import permission_classes, throttle_classes
from rest_framework import permissions, views, status
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from ...utils import uuid_validate
from ...secure import gpg_get_key
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
    if _uuid == '':
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
        'tags': [f'{tag.property_att.prefix}-{tag.value}' for tag in computer.tags.all()],
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


def get_key_repositories(request):
    """
    Returns the repositories public key
    """
    return HttpResponse(
        gpg_get_key('migasfree-repository'),
        content_type='text/plain'
    )


@permission_classes((permissions.AllowAny,))
class RepositoriesUrlTemplateView(views.APIView):
    serializer_class = None

    @extend_schema(
        description='Returns the repositories URL template'
                    ' (compatibility for migasfree-client <= 4.16)',
        responses={
            status.HTTP_200_OK: OpenApiTypes.STR
        },
        examples=[
            OpenApiExample(
                name='successfully response',
                value=f'http://<server>{settings.MEDIA_URL}<project>/{settings.MIGASFREE_REPOSITORY_TRAILING_PATH}',
                response_only=True,
            ),
        ],
        tags=['public'],
    )
    def post(self, request):
        protocol = 'https' if request.is_secure() else 'http'

        return Response(
            '{}://{{server}}{}{{project}}/{}'.format(
                protocol,
                settings.MEDIA_URL,
                settings.MIGASFREE_REPOSITORY_TRAILING_PATH
            ),
            content_type='text/plain'
        )


@permission_classes((permissions.AllowAny,))
@throttle_classes([UserRateThrottle])
class ServerInfoView(views.APIView):
    def post(self, request):
        """
        Returns server info
        """
        from ... import __version__, __author__, __contact__, __homepage__

        info = {
            'version': __version__,
            'author': __author__,
            'contact': __contact__,
            'homepage': __homepage__,
            'organization': settings.MIGASFREE_ORGANIZATION,
        }

        return Response(info)
