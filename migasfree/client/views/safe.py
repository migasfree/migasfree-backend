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

import logging

from django.conf import settings
from django.contrib import auth
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiExample, OpenApiTypes, extend_schema, inline_serializer
from rest_framework import permissions, status, views, viewsets
from rest_framework import serializers as drf_serializers
from rest_framework.decorators import action, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from ...app_catalog.models import Policy
from ...core.mixins import SafeConnectionMixin
from ...core.models import (
    Attribute,
    AttributeSet,
    BasicAttribute,
    Deployment,
    Domain,
    Property,
)
from ...model_update import update
from ...utils import (
    get_client_ip,
    remove_duplicates_preserving_order,
    replace_keys,
    uuid_change_format,
)
from .. import models, serializers, tasks
from ..messages import add_computer_message, remove_computer_messages

logger = logging.getLogger('migasfree')


def get_user_or_create(name, fullname, ip_address=None):
    user, created = models.User.objects.get_or_create(name=name, fullname=fullname)

    if created and ip_address:
        msg = _('User [%s] registered by IP [%s].') % (name, ip_address)
        models.Notification.objects.create(message=msg)

    return user


# TODO call when computer is updated
def is_computer_changed(computer, name, project, ip_address, uuid):
    # compatibility with client apiv4
    if not computer:
        computer = models.Computer.objects.create(name, project, uuid)
        models.Migration.objects.create(computer, project)

        if settings.MIGASFREE_NOTIFY_NEW_COMPUTER:
            models.Notification.objects.create(
                _('New Computer added id=[%s]: NAME=[%s] UUID=[%s]') % (computer.id, computer, computer.uuid)
            )
    # end compatibility with client apiv4

    if computer.project != project:
        models.PackageHistory.uninstall_computer_packages(computer.id)

        models.Migration.objects.create(computer=computer, project=project)
        computer.update_project(project)

    if settings.MIGASFREE_NOTIFY_CHANGE_NAME and (computer.name != name):
        msg = _('Computer id=[%s]: NAME [%s] changed by [%s]') % (computer.id, computer, name)
        models.Notification.objects.create(message=msg)
        computer.update_name(name)

    if settings.MIGASFREE_NOTIFY_CHANGE_IP and (computer.ip_address != ip_address):
        msg = _('Computer id=[%s]: IP [%s] changed by [%s]') % (computer.id, computer.ip_address, ip_address)
        models.Notification.objects.create(message=msg)
        computer.update_ip_address(ip_address)

    if settings.MIGASFREE_NOTIFY_CHANGE_UUID and (computer.uuid != uuid):
        msg = _('Computer id=[%s]: UUID [%s] changed by [%s]') % (computer.id, computer.uuid, uuid)
        models.Notification.objects.create(message=msg)
        computer.update_uuid(uuid)

    return computer


def get_computer(uuid, name):
    logger.debug('uuid: %s, name: %s', uuid, name)

    try:
        computer = models.Computer.objects.get(uuid=uuid)
        logger.debug('computer found by uuid')

        return computer
    except models.Computer.DoesNotExist:
        pass

    try:
        computer = models.Computer.objects.get(uuid=uuid_change_format(uuid))
        logger.debug('computer found by uuid (endian format changed)')

        return computer
    except models.Computer.DoesNotExist:
        pass

    computer = models.Computer.objects.filter(mac_address__icontains=uuid[-12:])
    if computer.count() == 1 and uuid[0:8] == '0' * 8:
        logger.debug('computer found by mac_address (in uuid format)')

        return computer.first()

    try:
        computer = models.Computer.objects.get(name=name)
        logger.debug('computer found by name')

        return computer
    except (models.Computer.DoesNotExist, models.Computer.MultipleObjectsReturned):
        return None


@extend_schema(tags=['safe'])
@permission_classes((permissions.AllowAny,))
@throttle_classes([UserRateThrottle])
class SafeEndOfTransmissionView(SafeConnectionMixin, views.APIView):
    @extend_schema(
        description='Returns 200 if ok, 404 if computer not found (requires JWT auth)',
        request={'id': OpenApiTypes.INT},
        responses={
            status.HTTP_200_OK: {'description': gettext('EOT OK')},
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
        examples=[
            OpenApiExample(
                name='successfully response',
                value=gettext('EOT OK'),
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        """
        claims = {"id": id}
        """
        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        remove_computer_messages(computer.id)

        if computer.status == 'available':
            models.Notification.objects.create(
                _('Computer [%s] with available status, has been synchronized') % computer
            )

        return Response(self.create_response(gettext('EOT OK')), status=status.HTTP_200_OK)


@extend_schema(tags=['safe'])
@permission_classes((permissions.AllowAny,))
@throttle_classes([UserRateThrottle])
class SafeSynchronizationView(SafeConnectionMixin, views.APIView):
    @extend_schema(
        description='Creates a computer synchronization (requires JWT auth)',
        request=inline_serializer(
            name='SafeSyncRequest',
            fields={
                'id': drf_serializers.IntegerField(),
                'start_date': drf_serializers.DateTimeField(),
                'consumer': drf_serializers.CharField(),
                'pms_status_ok': drf_serializers.BooleanField(),
            },
        ),
        responses={
            status.HTTP_201_CREATED: serializers.SynchronizationWriteSerializer,
            status.HTTP_400_BAD_REQUEST: {'description': 'Error in request'},
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
    )
    def post(self, request):
        """
        claims = {
            "id": id,
            "start_date": datetime,
            "consumer": string,
            "pms_status_ok": true|false
        }
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))
        self.verify_mtls_identity(request, computer.uuid)

        add_computer_message(computer, gettext('Getting synchronization...'))

        data = {
            'computer': computer.id,
            'user': computer.sync_user.id,
            'project': self.project.id,
            'start_date': claims.get('start_date'),
            'consumer': claims.get('consumer'),
            'pms_status_ok': claims.get('pms_status_ok', False),
        }
        serializer = serializers.SynchronizationWriteSerializer(data=data)

        add_computer_message(computer, gettext('Sending synchronization...'))

        if serializer.is_valid():
            serializer.save()

            return Response(self.create_response(serializer.data), status=status.HTTP_201_CREATED)

        return Response(self.create_response(serializer.errors), status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['safe'])
@permission_classes((permissions.AllowAny,))
@throttle_classes([UserRateThrottle])
class SafeComputerViewSet(SafeConnectionMixin, viewsets.ViewSet):
    @extend_schema(
        description='Creates or updates a computer (requires JWT auth)',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'uuid': {'type': 'string', 'format': 'uuid'},
                    'name': {'type': 'string'},
                    'ip_address': {'type': 'string', 'format': 'ipv4'},
                    'username': {'type': 'string'},
                    'password': {'type': 'string', 'format': 'password'},
                },
                'required': ['uuid', 'name', 'ip_address', 'username', 'password'],
            }
        },
        responses={
            status.HTTP_200_OK: {'description': 'Computer data updated'},
            status.HTTP_201_CREATED: serializers.ComputerCreateSerializer,
            status.HTTP_400_BAD_REQUEST: {'description': 'Error in request'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Computer cannot be registered'},
        },
    )
    def create(self, request):
        """
        claims = {
            'uuid': '01020304050607080910111213141516',
            'name': 'PC12345',
            'ip_address': '127.0.0.1',
            'username': 'admin',
            'password': 'admin'
        }
        """

        claims = self.get_claims(request.data)
        if not claims or not all(k in claims for k in ('uuid', 'name', 'ip_address', 'username', 'password')):
            return Response(self.create_response(gettext('Invalid Data')), status=status.HTTP_400_BAD_REQUEST)

        claims['project'] = self.project.id
        claims['forwarded_ip_address'] = get_client_ip(request)

        computer = get_computer(claims.get('uuid'), claims.get('name'))
        if computer:
            self.verify_mtls_identity(request, computer.uuid)
            computer = is_computer_changed(
                computer, claims.get('name'), self.project, claims.get('ip_address'), claims.get('uuid')
            )

            # change to default status
            computer.change_status(settings.MIGASFREE_DEFAULT_COMPUTER_STATUS)

            serializer = serializers.ComputerSerializer(computer, context={'request': request})
            return Response(self.create_response(serializer.data), status=status.HTTP_200_OK)

        user = auth.authenticate(username=claims.get('username'), password=claims.get('password'))
        if not self.project.auto_register_computers and (
            not user or not user.is_superuser or not user.has_perm('client.add_computer')
        ):
            return Response(
                self.create_response(gettext('Computer cannot be registered')), status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = serializers.ComputerCreateSerializer(data=claims, context={'request': request})
        if serializer.is_valid():
            computer = serializer.save()

            models.Migration.objects.create(computer=computer, project=self.project)

            if settings.MIGASFREE_NOTIFY_NEW_COMPUTER:
                msg = _('New Computer added id=[%(id)s]: NAME=[%(name)s] UUID=[%(uuid)s]') % {
                    'id': serializer.data.get('id'),
                    'name': serializer.data.get('name'),
                    'uuid': serializer.data.get('uuid'),
                }
                models.Notification.objects.create(message=msg)

            return Response(self.create_response(serializer.data), status=status.HTTP_201_CREATED)

        return Response(self.create_response(serializer.errors), status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description='Creates or updates a computer (requires JWT auth)',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'uuid': {'type': 'string', 'format': 'uuid'},
                    'name': {'type': 'string'},
                },
                'required': ['uuid', 'name'],
            }
        },
        responses={
            status.HTTP_200_OK: {
                'type': 'object',
                'id': {'type': 'integer'},
            },
            status.HTTP_400_BAD_REQUEST: {'description': 'Error in request'},
            status.HTTP_403_FORBIDDEN: {'description': 'Unsubscribed computer'},
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
        examples=[
            OpenApiExample(
                name='successfully response',
                value={'id': 23},
                response_only=True,
            ),
        ],
    )
    @action(methods=['post'], detail=False, url_path='id')
    def id_(self, request):
        """
        claims = {
            'uuid': '01020304050607080910111213141516',
            'name': 'PC12345'
        }
        Returns a computer ID (or 404 if not found)
        """

        claims = self.get_claims(request.data)

        if isinstance(claims, str):
            return Response(self.create_response(claims), status=status.HTTP_400_BAD_REQUEST)

        if not claims or 'uuid' not in claims or 'name' not in claims:
            return Response(self.create_response(gettext('Malformed claims')), status=status.HTTP_400_BAD_REQUEST)

        computer = get_computer(claims['uuid'], claims['name'])
        if not computer:
            return Response(self.create_response(gettext('Computer not found')), status=status.HTTP_404_NOT_FOUND)

        if computer.status == 'unsubscribed':
            models.Error.objects.create(
                computer,
                computer.project,
                f'{get_client_ip(request)} - id - {gettext("Unsubscribed computer")}',
            )
            return Response(self.create_response(gettext('Unsubscribed computer')), status=status.HTTP_403_FORBIDDEN)

        if computer.project.id != self.project.id:
            return Response(
                self.create_response(
                    gettext('Unexpected Computer Project (%s). Expected %s')
                    % (self.project.name, computer.project.name)
                ),
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(self.create_response(computer.id), status=status.HTTP_200_OK)

    @extend_schema(
        description='Returns enabled properties for a given computer (requires JWT auth)',
        request={'id': OpenApiTypes.INT},
        responses={
            status.HTTP_200_OK: {
                'type': 'object',
                'properties': {
                    'prefix': {'type': 'string'},
                    'language': {'type': 'string'},
                    'code': {'type': 'string'},
                },
            },
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
    )
    @action(methods=['post'], detail=False)
    def properties(self, request):
        """
        claims = {'id': 1}
        """
        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        add_computer_message(computer, gettext('Getting properties...'))

        properties = Property.enabled_client_properties(computer.get_all_attributes())

        add_computer_message(computer, gettext('Sending properties...'))

        return Response(self.create_response(properties), status=status.HTTP_200_OK)

    @extend_schema(
        description='Process and record sync attributes for a given computer (requires JWT auth)',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'uuid': {'type': 'string', 'format': 'uuid'},
                    'name': {'type': 'string'},
                    'ip_address': {'type': 'string', 'format': 'ipv4'},
                    'sync_user': {'type': 'string'},
                    'sync_fullname': {'type': 'string'},
                    'sync_attributes': {'type': 'object', 'additionalProperties': {'type': 'string'}},
                },
                'required': [
                    'id',
                    'uuid',
                    'name',
                    'ip_address',
                    'sync_user',
                    'sync_fullname',
                    'sync_attributes',
                ],
            }
        },
        responses={
            status.HTTP_201_CREATED: serializers.ComputerSerializer,
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
    )
    @action(methods=['post'], detail=False)
    def attributes(self, request):
        """
        claims = {
            'id', 1,
            'uuid': '01020304050607080910111213141516',
            'name': 'PC12345',
            'ip_address': '192.168.1.33',
            'sync_user': 'inigo',
            'sync_fullname': 'Íñigo Montoya',
            'sync_attributes': {
                'NET': '192.168.1.0/24',  # prefix: value
                ...,
            }
        }
        """
        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))
        self.verify_mtls_identity(request, computer.uuid)

        add_computer_message(computer, gettext('Getting attributes...'))

        is_computer_changed(computer, claims.get('name'), self.project, claims.get('ip_address'), claims.get('uuid'))

        user = get_user_or_create(claims.get('sync_user'), claims.get('sync_fullname'), claims.get('ip_address'))
        user.update_fullname(claims.get('sync_fullname'))

        computer.sync_attributes.clear()

        # features
        for prefix, value in claims.get('sync_attributes').items():
            client_property = Property.objects.get(prefix=prefix)
            if client_property.sort == 'client':
                computer.sync_attributes.add(*Attribute.process_kind_property(client_property, value))

        # Domain attribute
        computer.sync_attributes.add(*Domain.process(computer.get_all_attributes()))

        # tags
        for tag in computer.tags.filter(property_att__enabled=True):
            computer.sync_attributes.add(*Attribute.process_kind_property(tag.property_att, tag.value))

        # basic attributes
        computer.sync_attributes.add(
            *BasicAttribute.process(
                id=computer.id,
                ip_address=claims.get('ip_address'),
                project=computer.project.name,
                platform=computer.project.platform.name,
                user=user.name,
                description=computer.get_cid_description(),
            )
        )

        # attribute sets
        computer.sync_attributes.add(*AttributeSet.process(computer.get_all_attributes()))

        update(
            computer,
            uuid=claims.get('uuid'),
            name=claims.get('name'),
            fqdn=claims.get('fqdn'),
            ip_address=claims.get('ip_address'),
            forwarded_ip_address=get_client_ip(request),
            sync_user=user,
            sync_start_date=timezone.localtime(timezone.now()),
        )

        serializer = serializers.ComputerSerializer(computer, context={'request': request})

        add_computer_message(computer, gettext('Sending attributes...'))

        return Response(self.create_response(serializer.data), status=status.HTTP_201_CREATED)

    @extend_schema(
        description='Returns computer available repositories list (requires JWT auth)',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer', 'description': 'Computer ID'},
                },
                'required': ['id'],
            }
        },
        responses={
            status.HTTP_200_OK: {
                'type': 'object',
                'properties': {'name': {'type': 'string'}, 'source_template': {'type': 'string'}},
            },
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
    )
    @action(methods=['post'], detail=False)
    def repositories(self, request):
        """
        claims = {'id': 1}

        Returns: [{"name": slug, "source_template": "template"}, ...]
        """
        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        add_computer_message(computer, gettext('Getting repositories...'))

        ret = [
            {'name': repo.slug, 'source_template': repo.source_template()}
            for repo in Deployment.available_deployments(computer, computer.get_all_attributes())
        ]

        add_computer_message(computer, gettext('Sending repositories...'))

        return Response(self.create_response(ret), status=status.HTTP_200_OK)

    @extend_schema(
        description='Returns computer fault definitions list (requires JWT auth)',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer', 'description': 'Computer ID'},
                },
                'required': ['id'],
            }
        },
        responses={
            status.HTTP_200_OK: serializers.FaultDefinitionForAttributesSerializer(many=True),
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
        examples=[
            OpenApiExample(
                'Example request',
                value={'id': 1},
                request_only=True,
            ),
            OpenApiExample(
                'Example response',
                value=[
                    {'name': 'SampleFaultDefinition', 'language': 'python', 'code': 'print("This is a sample code.")'}
                ],
                response_only=True,
            ),
        ],
    )
    @action(methods=['post'], detail=False, url_path='faults/definitions')
    def fault_definitions(self, request):
        """
        claims = {'id': 1}

        Returns: [
            {
                'name': 'xxx',
                'language': 'bash' | 'php' | 'python' | 'ruby' | 'perl' | 'cmd' | 'powershell',
                'code': 'xxxx'
            },
            ...
        ]
        """
        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        add_computer_message(computer, gettext('Getting fault definitions...'))

        results = models.FaultDefinition.enabled_for_attributes(computer.get_all_attributes())
        ret = [serializers.FaultDefinitionForAttributesSerializer(item).data for item in results]

        add_computer_message(computer, gettext('Sending fault definitions...'))

        return Response(self.create_response(list(ret)), status=status.HTTP_200_OK)

    @extend_schema(
        description='Process and record faults for a given computer (requires JWT auth)',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer', 'description': 'Computer ID'},
                    'faults': {
                        'type': 'object',
                        'description': 'A dictionary of fault names and their results.',
                        'propertyNames': {'type': 'string', 'description': 'Name of the fault'},
                        'additionalProperties': {
                            'type': 'string',
                            'description': 'Result of the fault (empty string = no error)',
                        },
                    },
                },
                'required': ['id', 'faults'],
            }
        },
        responses={
            status.HTTP_200_OK: serializers.FaultSerializer(many=True),
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
        examples=[
            OpenApiExample(
                'Example request',
                value={
                    'id': 1,
                    'faults': {
                        'Low Available Space On Home Partition': '',
                        'Low Available Space On System Partition': '95%',
                    },
                },
                request_only=True,
            ),
        ],
    )
    @action(methods=['post'], detail=False)
    def faults(self, request):
        """
        claims = {
            'id': 1,
            'faults': {
                'Low Available Space On Home Partition': '',  # name: result
                'Low Available Space On System Partition': '95%',
                ...
            }
        }
        """
        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))
        self.verify_mtls_identity(request, computer.uuid)

        add_computer_message(computer, gettext('Getting faults...'))

        ret = []
        for name, result in claims.get('faults').items():
            try:
                definition = models.FaultDefinition.objects.get(name=name)
            except ObjectDoesNotExist:
                continue

            if result != '':  # something went wrong
                obj = models.Fault.objects.create(computer, definition, result)
                serializer = serializers.FaultSerializer(obj)
                ret.append(serializer.data)

        add_computer_message(computer, gettext('Sending faults...'))

        return Response(self.create_response(list(ret)), status=status.HTTP_200_OK)

    @extend_schema(
        description='Process and record errors for a given computer (requires JWT auth)',
        request=serializers.ErrorSafeWriteSerializer,
        responses={
            status.HTTP_201_CREATED: serializers.ErrorSafeWriteSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiTypes.OBJECT,
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
        examples=[
            OpenApiExample(
                'Claim example',
                summary='Example claim object',
                description='A sample claim object that will be processed.',
                value={'id': 1, 'description': 'could not connect to host'},
                request_only=True,
            ),
            OpenApiExample(
                'Success response',
                summary='Claim processed successfully',
                description='The response when a claim is processed successfully.',
                value={'id': 1, 'description': 'could not connect to host', 'computer': 123, 'project': 456},
                response_only=True,
            ),
            OpenApiExample(
                'Error response',
                summary='Claim validation failed',
                description='The response when the claim data is invalid.',
                value={'description': ['This field may not be null.']},
                response_only=True,
            ),
        ],
    )
    @action(methods=['post'], detail=False)
    def errors(self, request):
        """
        claims = {
            'id': 1,
            'description': 'could not connect to host'
        }
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))
        self.verify_mtls_identity(request, computer.uuid)
        claims['computer'] = computer.id
        claims['project'] = self.project.id

        add_computer_message(computer, gettext('Getting errors...'))

        serializer = serializers.ErrorSafeWriteSerializer(data=claims)

        add_computer_message(computer, gettext('Sending errors...'))

        if serializer.is_valid():
            serializer.save()
            return Response(self.create_response(serializer.data), status=status.HTTP_201_CREATED)

        return Response(self.create_response(serializer.errors), status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description='Returns mandatory packages for a computer (requires JWT auth). '
        'If no packages are defined an empty list is returned.',
        request={
            'id': OpenApiTypes.INT,
        },
        responses={
            status.HTTP_200_OK: {
                'type': 'object',
                'properties': {
                    'install': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'Packages to install.',
                    },
                    'remove': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'Packages to remove.',
                    },
                },
                'example': {'install': ['one', 'two'], 'remove': ['three']},
            },
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
    )
    @action(methods=['post'], detail=False, url_path='packages/mandatory')
    def mandatory_pkgs(self, request):
        """
        claims = {'id': 1}

        Returns: {
            "install": ["one", "two"],
            "remove": ["three"]
        }
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        add_computer_message(computer, gettext('Getting mandatory packages...'))

        pkgs = Deployment.available_deployments(computer, computer.get_all_attributes()).values_list(
            'packages_to_install', 'packages_to_remove'
        )

        add_computer_message(computer, gettext('Sending mandatory packages...'))

        if pkgs:
            install = []
            remove = []
            for install_item, remove_item in pkgs:
                if install_item:
                    install.extend([x for x in install_item.split('\n') if x])

                if remove_item:
                    remove.extend([x for x in remove_item.split('\n') if x])

            # policies
            policy_pkg_to_install, policy_pkg_to_remove = Policy.get_packages(computer)
            install.extend([x['package'] for x in policy_pkg_to_install])
            remove.extend([x['package'] for x in policy_pkg_to_remove])

            response = {
                'install': remove_duplicates_preserving_order(install),
                'remove': remove_duplicates_preserving_order(remove),
            }

            return Response(self.create_response(response), status=status.HTTP_200_OK)

        return Response(self.create_response({'install': [], 'remove': []}), status.HTTP_200_OK)

    @extend_schema(
        description='Returns the list of tags assigned to a computer (requires JWT auth).',
        request={
            'id': OpenApiTypes.INT,
        },
        responses={
            status.HTTP_200_OK: {
                'type': 'object',
                'properties': {
                    'tags': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'List of tags assigned to the computer.',
                    },
                },
                'example': {'tags': ['PR1-value1', 'PR2-value2']},
            },
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
    )
    @action(methods=['post'], detail=False, url_path='tags/assigned')
    def assigned_tags(self, request):
        """
        claims = {'id': 1}

        Returns: {
            "tags": ["PR1-value1", "PR2-value2"]
        }
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        add_computer_message(computer, gettext('Getting assigned tags...'))

        response = [str(tag) for tag in computer.tags.all()]

        add_computer_message(computer, gettext('Sending assigned tags...'))

        return Response(self.create_response(response), status=status.HTTP_200_OK)

    @extend_schema(
        description='Returns all tags that are available for a computer (requires JWT auth). '
        'The response is a dictionary where each key is a tag name '
        'and the value is a list of possible tag values.',
        request={
            'id': OpenApiTypes.INT,
        },
        responses={
            status.HTTP_200_OK: {
                'type': 'object',
                'additionalProperties': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Possible values for the tag name (key).',
                },
                'example': {
                    'name': ['PR1-value1', 'PR2-value2'],
                    'name2': ['PR3-value3'],
                    # …
                },
            },
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
    )
    @action(methods=['post'], detail=False, url_path='tags/available')
    def available_tags(self, request):
        """
        claims = {'id': 1}

        Returns: {
            "name": ["PR1-value1", "PR2-value2"]
            "name2": ["PR3-value3"]
            ...
        }
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        add_computer_message(computer, gettext('Getting available tags...'))

        available = {}

        # Computer tags
        for tag in computer.tags.all():
            """ TODO think about this!
            available.setdefault(tag.property_att.name, []).append(str(tag))
            """

            # if tag is a domain, includes all domain's tags
            if tag.property_att.prefix == 'DMN':
                for tag_dmn in Domain.objects.get(name=tag.value.split('.')[0]).get_tags():
                    available.setdefault(tag_dmn.property_att.name, []).append(str(tag_dmn))

        # Deployment tags
        for deploy in Deployment.objects.filter(project__id=computer.project.id).filter(enabled=True):
            for tag in deploy.included_attributes.filter(property_att__sort='server').filter(
                property_att__enabled=True
            ):
                available.setdefault(tag.property_att.name, []).append(str(tag))

        # Domain Tags
        for domain in Domain.objects.filter(
            Q(included_attributes__in=computer.sync_attributes.all())
            & ~Q(excluded_attributes__in=computer.sync_attributes.all())
        ):
            for tag in domain.tags.all():
                available.setdefault(tag.property_att.name, []).append(str(tag))

        add_computer_message(computer, gettext('Sending available tags...'))

        return Response(self.create_response(available), status=status.HTTP_200_OK)

    @extend_schema(
        description='Assigns a list of tags to a computer and returns the packages that must be '
        'pre-installed, installed or removed as a result (requires JWT auth).',
        request={
            'id': OpenApiTypes.INT,  # computer identifier
            'tags': {
                'type': 'array',
                'items': {'type': 'string'},
                'description': 'List of tag strings in the form "<prefix>-<value>".',
            },
        },
        responses={
            status.HTTP_200_OK: {
                'type': 'object',
                'properties': {
                    'preinstall': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'Packages that must be pre-installed.',
                    },
                    'install': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'Packages to install.',
                    },
                    'remove': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'Packages to remove.',
                    },
                },
                'example': {
                    'preinstall': ['four', 'five'],
                    'install': ['one', 'two'],
                    'remove': ['three'],
                },
            },
            status.HTTP_400_BAD_REQUEST: {'description': 'Invalid tags supplied'},
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
    )
    @action(methods=['post'], detail=False)
    def tags(self, request):
        """
        claims = {
            'id': 1,
            'tags': ['AUL-casablanca']  # prefix-value
        }

        Returns: {
            "preinstall": ["four", "five"],
            "install": ["one", "two"],
            "remove": ["three"]
        }
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))
        self.verify_mtls_identity(request, computer.uuid)

        add_computer_message(computer, gettext('Getting tags...'))

        computer_tags_ids = computer.tags.values_list('id', flat=True)
        tags = claims.get('tags')
        tag_objs = Attribute.objects.filter_by_prefix_value(tags)
        if not tag_objs:
            return Response(self.create_response(gettext('Invalid tags')), status=status.HTTP_400_BAD_REQUEST)

        computer.tags.set(tag_objs)
        tag_ids = tag_objs.values_list('id', flat=True)

        old_tags = list(set(computer_tags_ids) - set(tag_ids))
        new_tags = list(set(tag_ids) - set(computer_tags_ids))
        intersection_tags = list(set(computer_tags_ids).intersection(tag_ids))

        preinstall = []
        install = []
        remove = []

        # Old deploys
        old_deploys = Deployment.available_deployments(computer, old_tags)
        pkgs = old_deploys.values_list(
            'packages_to_install', 'default_preincluded_packages', 'default_included_packages'
        )
        for packages_to_install, default_preincluded_packages, default_included_packages in pkgs:
            remove.extend(pkg for pkg in packages_to_install.split('\n') if pkg)
            remove.extend(pkg for pkg in default_preincluded_packages.split('\n') if pkg)
            remove.extend(pkg for pkg in default_included_packages.split('\n') if pkg)

        pkgs = old_deploys.values_list('packages_to_remove', 'default_excluded_packages')
        for packages_to_remove, default_excluded_packages in pkgs:
            install.extend(pkg for pkg in packages_to_remove.split('\n') if pkg)
            install.extend(pkg for pkg in default_excluded_packages.split('\n') if pkg)

        # New deploys
        new_deploys = Deployment.available_deployments(computer, new_tags + intersection_tags)
        pkgs = new_deploys.values_list('packages_to_remove', 'default_excluded_packages')
        for packages_to_remove, default_excluded_packages in pkgs:
            remove.extend(pkg for pkg in packages_to_remove.split('\n') if pkg)
            remove.extend(pkg for pkg in default_excluded_packages.split('\n') if pkg)

        pkgs = new_deploys.values_list('packages_to_install', 'default_included_packages')
        for packages_to_install, default_included_packages in pkgs:
            install.extend(pkg for pkg in packages_to_install.split('\n') if pkg)
            install.extend(pkg for pkg in default_included_packages.split('\n') if pkg)

        pkgs = new_deploys.values_list('default_preincluded_packages', flat=True)
        for default_preincluded_packages in pkgs:
            preinstall.extend(pkg for pkg in default_preincluded_packages.split('\n') if pkg)

        ret = {
            'preinstall': remove_duplicates_preserving_order(preinstall),
            'install': remove_duplicates_preserving_order(install),
            'remove': remove_duplicates_preserving_order(remove),
        }

        add_computer_message(computer, gettext('Sending tags...'))

        return Response(self.create_response(ret), status=status.HTTP_200_OK)

    @extend_schema(
        description='Returns basic label information for a computer (requires JWT auth).',
        request={
            'id': OpenApiTypes.INT,
        },
        responses={
            status.HTTP_200_OK: {
                'type': 'object',
                'properties': {
                    'uuid': {
                        'type': 'string',
                        'format': 'uuid',
                        'description': 'Unique identifier of the computer.',
                    },
                    'name': {
                        'type': 'string',
                        'description': 'Human-readable name of the computer.',
                    },
                    'search': {
                        'type': 'string',
                        'description': 'String representation of the computer (used for searches).',
                    },
                    'helpdesk': {
                        'type': 'string',
                        'description': 'Helpdesk URL or identifier defined in settings.',
                    },
                },
                'example': {
                    'uuid': '123e4567-e89b-12d3-a456-426614174000',
                    'name': 'my-computer',
                    'search': 'my-computer (001)',
                    'helpdesk': 'https://helpdesk.example.com',
                },
            },
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
    )
    @action(methods=['post'], detail=False)
    def label(self, request):
        """
        claims = {
            'id': 1,
        }

        Returns: {
            "uuid": string,
            "name": string,
            "search": string,
            "helpdesk": string
        }
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        add_computer_message(computer, gettext('Getting label...'))

        ret = {
            'uuid': computer.uuid,
            'name': computer.name,
            'search': computer.__str__(),
            'helpdesk': settings.MIGASFREE_HELP_DESK,
        }

        add_computer_message(computer, gettext('Sending label...'))

        return Response(self.create_response(ret), status=status.HTTP_200_OK)

    @extend_schema(
        description='Indicates whether a hardware capture is required for the given computer (requires JWT auth).',
        request={
            'id': OpenApiTypes.INT,
        },
        responses={
            status.HTTP_200_OK: {
                'type': 'object',
                'properties': {
                    'capture': {
                        'type': 'boolean',
                        'description': 'True if a hardware capture is required, otherwise False.',
                    },
                },
                'example': {'capture': True},
            },
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
    )
    @action(methods=['post'], detail=False, url_path='hardware/required')
    def hardware_capture_is_required(self, request):
        """
        claims = {'id': 1}

        Returns: {
            "capture": true | false
        }
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        add_computer_message(computer, gettext('Getting hardware capture is required...'))

        capture = computer.hardware_capture_is_required()

        add_computer_message(computer, gettext('Sending hardware capture...'))

        return Response(self.create_response({'capture': capture}), status=status.HTTP_200_OK)

    @extend_schema(
        description='Receives software inventory and history for a computer (requires JWT auth). '
        "The endpoint updates the computer's software records and returns a confirmation message.",
        request={
            'id': OpenApiTypes.INT,
            'inventory': {
                'type': 'array',
                'items': {'type': 'string'},
                'description': 'List of currently installed packages (optional).',
            },
            'history': {
                'type': 'object',
                'properties': {
                    'installed': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'Packages that were installed since the last report.',
                    },
                    'uninstalled': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'Packages that were removed since the last report.',
                    },
                },
                'description': 'Software change history (optional).',
            },
        },
        responses={
            status.HTTP_200_OK: {
                'type': 'string',
                'description': 'Acknowledgement that the data was received.',
                'example': 'Data received',
            },
            status.HTTP_400_BAD_REQUEST: {
                'type': 'string',
                'description': 'Bad request: neither *inventory* nor *history* provided.',
                'example': 'Bad request',
            },
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
    )
    @action(methods=['post'], detail=False)
    def software(self, request):
        """
        claims = {
            'id', 1,
            'inventory': ['asdasd', 'asdasdsd', 'asdafsdsd', ...],
            'history': {
                'installed': ['asdasd', 'asddda', ...],
                'uninstalled': ['dada', ...]
            }
        }
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))
        self.verify_mtls_identity(request, computer.uuid)

        add_computer_message(computer, gettext('Getting software...'))

        if 'inventory' not in claims and 'history' not in claims:
            return Response(self.create_response(gettext('Bad request')), status=status.HTTP_400_BAD_REQUEST)

        computer.update_software_history(claims.get('history'))
        tasks.update_software_inventory.delay(computer.id, claims.get('inventory'))

        add_computer_message(computer, gettext('Sending software...'))

        return Response(self.create_response(gettext('Data received')), status=status.HTTP_200_OK)

    @extend_schema(
        description='Returns a list of logical devices for a given computer along with the default logical device ID '
        '(requires JWT auth)',
        request={'id': OpenApiTypes.INT},
        responses={
            status.HTTP_200_OK: {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'logical': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'printer': {
                                        'type': 'object',
                                        'properties': {
                                            'id': {'type': 'integer'},
                                            'name': {'type': 'string'},
                                            'model': {'type': 'string'},
                                            'driver': {'type': 'string'},
                                            'capability': {'type': 'string'},
                                            'manufacturer': {'type': 'string'},
                                            'packages': {'type': 'array', 'items': {'type': 'string'}},
                                            'connection': {'type': 'object'},
                                        },
                                        'required': [
                                            'id',
                                            'name',
                                            'model',
                                            'driver',
                                            'capability',
                                            'manufacturer',
                                            'packages',
                                            'connection',
                                        ],
                                    }
                                },
                                'required': ['printer'],
                            },
                        },
                        'default': {'type': 'integer'},
                    },
                    'required': ['logical', 'default'],
                },
                'example': {
                    'logical': [
                        {
                            'printer': {
                                'id': 99,
                                'name': 'OfficePrinter-01',
                                'model': 'LaserJet 5000',
                                'driver': 'hp-laserjet',
                                'capability': 'color',
                                'manufacturer': 'HP',
                                'packages': ['hp-driver', 'printer-utils'],
                                'connection': {},
                            }
                        },
                        {
                            'printer': {
                                'id': 100,
                                'name': 'OfficePrinter-02',
                                'model': 'LaserJet 5000',
                                'driver': 'hp-laserjet',
                                'capability': 'color',
                                'manufacturer': 'HP',
                                'packages': ['hp-driver', 'printer-utils'],
                                'connection': {},
                            }
                        },
                    ],
                    'default': 99,
                },
            },
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
    )
    @action(methods=['post'], detail=False)
    def devices(self, request):
        """
        claims = {'id': 1}

        Returns: {
            "logical": [
                {
                    "printer": {
                        "id": 99,
                        "name": "xxxx",
                        "model": "xxxx",
                        "driver": "xxxx",
                        "capability": "xxxx",
                        "manufacturer": "xxxx",
                        "packages": ["pkg1", "pkg2"],
                        connection: {}
                    }
                },
                {
                    "printer": {
                        ...
                    }
                }
                ...
            ],
            "default": int
        }
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        logical_devices = [device.as_dict(computer.project) for device in computer.logical_devices()]

        default_logical_device = 0
        if computer.default_logical_device:
            default_logical_device = computer.default_logical_device.id

        logger.debug('logical devices: %s', logical_devices)
        logger.debug('default logical device: %d', default_logical_device)

        response = {
            'logical': logical_devices,
            'default': default_logical_device,
        }

        return Response(self.create_response(response), status=status.HTTP_200_OK)

    @extend_schema(
        description='Returns the list of traits (attributes) associated with a computer (requires JWT auth).',
        request={
            'id': OpenApiTypes.INT,
        },
        responses={
            status.HTTP_200_OK: {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer', 'description': 'Trait identifier.'},
                        'description': {'type': 'string', 'description': 'Human readable description.'},
                        'value': {'type': 'string', 'description': 'Current value of the trait.'},
                        'name': {'type': 'string', 'description': 'Trait name (property_att.name).'},
                        'prefix': {'type': 'string', 'description': 'Trait prefix (property_att.prefix).'},
                        'sort': {'type': 'string', 'description': 'Trait sort order (property_att.sort).'},
                    },
                    'example': {
                        'id': 1,
                        'description': 'lorem ipsum',
                        'value': 'x',
                        'name': 'xxxx',
                        'prefix': 'xxx',
                        'sort': 'xxxxxx',
                    },
                },
                'description': 'List of trait objects.',
            },
            status.HTTP_404_NOT_FOUND: {'description': 'Computer not found'},
        },
    )
    @action(methods=['post'], detail=False)
    def traits(self, request):
        """
        claims = {'id': 1}

        Returns: {
            [
                {
                    'id': 1,
                    'description': 'lorem ipsum',
                    'value': 'x',
                    'name': 'xxxx',
                    'prefix': 'xxx',
                    'sort': 'xxxxxx'
                },
                ...
            ]
        }
        """
        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        add_computer_message(computer, gettext('Getting traits...'))

        attributes = replace_keys(
            list(
                Attribute.objects.filter(computer__id=computer.id).values(
                    'id', 'description', 'value', 'property_att__name', 'property_att__prefix', 'property_att__sort'
                )
            ),
            {'property_att__name': 'name', 'property_att__prefix': 'prefix', 'property_att__sort': 'sort'},
        )

        add_computer_message(computer, gettext('Sending traits...'))

        return Response(self.create_response(attributes), status=status.HTTP_200_OK)
