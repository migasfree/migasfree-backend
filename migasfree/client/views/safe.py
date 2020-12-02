# -*- coding: utf-8 *-*

# Copyright (c) 2015-2020 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2020 Alberto Gacías <alberto@migasfree.org>
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

from datetime import datetime
from six import iteritems

from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext, gettext_lazy as _
from rest_framework import viewsets, status, views, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from django_redis import get_redis_connection

from migasfree.utils import (
    uuid_change_format, get_client_ip,
    remove_duplicates_preserving_order
)
from migasfree.model_update import update
from migasfree.core.mixins import SafeConnectionMixin
from migasfree.core.models import (
    Deployment, Property, Domain,
    Attribute, BasicAttribute, AttributeSet,
)
from migasfree.app_catalog.models import Policy

from .. import models, serializers, tasks

import logging
logger = logging.getLogger('migasfree')


def add_computer_message(computer, message):
    con = get_redis_connection()
    con.hmset(
        'migasfree:msg:%d' % computer.id, {
            'date': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'),
            'computer_id': computer.id,
            'computer_name': computer.__str__(),
            'project_id': computer.project.id,
            'project_name': computer.project.name,
            'ip_address': computer.ip_address,
            'user_id': computer.sync_user.id,
            'user_name': computer.sync_user.__str__(),
            'msg': message
        }
    )
    con.sadd('migasfree:watch:msg', computer.id)


def remove_computer_messages(computer_id):
    con = get_redis_connection()
    keys = con.hkeys('migasfree:msg:%d' % computer_id)
    con.hdel('migasfree:msg:%d' % computer_id, *keys)
    con.srem('migasfree:watch:msg', computer_id)


def get_user_or_create(name, fullname, ip_address=None):
    user = models.User.objects.filter(name=name, fullname=fullname)
    if not user:
        user = models.User.objects.create(name=name, fullname=fullname)

        if ip_address:
            msg = _('User [%s] registered by IP [%s].') % (
                name, ip_address
            )
            models.Notification.objects.create(message=msg)

        return user
    else:
        return user[0]


# TODO call when computer is updated
def is_computer_changed(computer, name, project, ip_address, uuid):
    if computer.project != project:
        models.Migration.objects.create(
            computer=computer,
            project=project
        )
        computer.update_project(project)

    if settings.MIGASFREE_NOTIFY_CHANGE_NAME and (computer.name != name):
        msg = _("Computer id=[%s]: NAME [%s] changed by [%s]") % (
            computer.id,
            computer,
            name
        )
        models.Notification.objects.create(message=msg)
        computer.update_name(name)

    if settings.MIGASFREE_NOTIFY_CHANGE_IP and (computer.ip_address != ip_address):
        msg = _("Computer id=[%s]: IP [%s] changed by [%s]") % (
            computer.id,
            computer.ip_address,
            ip_address
        )
        models.Notification.objects.create(message=msg)
        computer.update_ip_address(ip_address)

    if settings.MIGASFREE_NOTIFY_CHANGE_UUID and (computer.uuid != uuid):
        msg = _("Computer id=[%s]: UUID [%s] changed by [%s]") % (
            computer.id,
            computer.uuid,
            uuid
        )
        models.Notification.objects.create(message=msg)
        computer.update_uuid(uuid)


def get_computer(uuid, name):
    logger.debug('uuid: %s, name: %s' % (uuid, name))

    try:
        computer = models.Computer.objects.get(uuid=uuid)
        logger.debug('computer found by uuid')

        return computer
    except models.Computer.DoesNotExist:
        pass

    try:
        computer = models.Computer.objects.get(
            uuid=uuid_change_format(uuid)
        )
        logger.debug('computer found by uuid (endian format changed)')

        return computer
    except models.Computer.DoesNotExist:
        pass

    computer = models.Computer.objects.filter(mac_address__icontains=uuid[-12:])
    if computer.count() == 1 and uuid[0:8] == '0'*8:
        logger.debug('computer found by mac_address (in uuid format)')

        return computer.first()

    try:
        computer = models.Computer.objects.get(name=name)
        logger.debug('computer found by name')

        return computer
    except (
        models.Computer.DoesNotExist,
        models.Computer.MultipleObjectsReturned
    ):
        return None


@permission_classes((permissions.AllowAny,))
class SafeEndOfTransmissionView(SafeConnectionMixin, views.APIView):
    def post(self, request, format=None):
        """
        claims = {"id": id}

        Returns 200 if ok, 404 if computer not found
        """
        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        remove_computer_messages(computer.id)

        if computer.status == 'available':
            models.Notification.objects.create(
                _('Computer [%s] with available status, has been synchronized')
                % computer
            )

        return Response(
            self.create_response(gettext('EOT OK')),
            status=status.HTTP_200_OK
        )


@permission_classes((permissions.AllowAny,))
class SafeSynchronizationView(SafeConnectionMixin, views.APIView):
    def post(self, request, format=None):
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

        add_computer_message(
            computer, gettext('Sending synchronization response...')
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                self.create_response(serializer.data),
                status=status.HTTP_201_CREATED
            )

        return Response(
            self.create_response(serializer.errors),
            status=status.HTTP_400_BAD_REQUEST
        )


@permission_classes((permissions.AllowAny,))
class SafeComputerViewSet(SafeConnectionMixin, viewsets.ViewSet):
    def create(self, request, format=None):
        """
        claims = {
            'uuid': '01020304050607080910111213141516',
            'name': 'PC12345',
            'ip_address': '127.0.0.1'
        }
        """

        claims = self.get_claims(request.data)
        claims['project'] = self.project.id
        claims['forwarded_ip_address'] = get_client_ip(request)

        computer = get_computer(claims.get('uuid'), claims.get('name'))
        if computer:
            serializer = serializers.ComputerSerializer(
                computer,
                context={'request': request}
            )
            return Response(
                self.create_response(serializer.data),
                status=status.HTTP_200_OK
            )

        serializer = serializers.ComputerCreateSerializer(
            data=claims,
            context={'request': request}
        )
        if serializer.is_valid():
            computer = serializer.save()

            models.Migration.objects.create(
                computer=computer,
                project=self.project
            )

            if settings.MIGASFREE_NOTIFY_NEW_COMPUTER:
                msg = _("New Computer added id=[%s]: NAME=[%s] UUID=[%s]") % (
                    serializer.data.get('id'),
                    serializer.data.get('name'),
                    serializer.data.get('uuid')
                )
                models.Notification.objects.create(message=msg)

            return Response(
                self.create_response(serializer.data),
                status=status.HTTP_201_CREATED
            )

        return Response(
            self.create_response(serializer.errors),
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(methods=['post'], detail=False)
    def id(self, request, format=None):
        """
        claims = {
            'uuid': '01020304050607080910111213141516',
            'name': 'PC12345'
        }
        Returns a computer ID (or 404 if not found)
        """

        claims = self.get_claims(request.data)

        if not claims or 'uuid' not in claims.keys() or 'name' not in claims.keys():
            return Response(
                self.create_response(gettext('Malformed claims')),
                status=status.HTTP_400_BAD_REQUEST
            )

        computer = get_computer(claims['uuid'], claims['name'])
        if not computer:
            return Response(
                self.create_response(gettext('Computer not found')),
                status=status.HTTP_404_NOT_FOUND
            )

        if computer.status == 'unsubscribed':
            models.Error.objects.create(
                computer,
                computer.project,
                '{} - {} - {}'.format(
                    get_client_ip(request),
                    'id',
                    gettext('Unsubscribed computer')
                )
            )
            return Response(
                self.create_response(
                    gettext('Unsubscribed computer')
                ),
                status=status.HTTP_403_FORBIDDEN
            )

        if computer.project.id != self.project.id:
            return Response(
                self.create_response(
                    gettext(
                        'Unexpected Computer Project (%s). Expected %s'
                    ) % (self.project.name, computer.project.name)
                ),
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(
            self.create_response(computer.id),
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=False)
    def properties(self, request, format=None):
        """
        claims = {'id': 1}

        Returns: {
            [
                {
                    'prefix': 'xxx',
                    'language': 'bash' | 'php' | 'python' | 'ruby' | 'perl',
                    'code': 'xxxx'
                },
                ...
            ]
        }
        """
        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        add_computer_message(computer, gettext('Getting properties...'))

        properties = Property.enabled_client_properties()

        add_computer_message(computer, gettext('Sending properties...'))

        if properties:
            return Response(
                self.create_response(properties),
                status=status.HTTP_200_OK
            )

        return Response(
            self.create_response('There are not properties'),
            status=status.HTTP_404_NOT_FOUND
        )

    @action(methods=['post'], detail=False)
    def attributes(self, request, format=None):
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

        add_computer_message(computer, gettext('Getting attributes...'))

        is_computer_changed(
            computer,
            claims.get('name'),
            self.project,
            claims.get('ip_address'),
            claims.get('uuid')
        )

        user = get_user_or_create(
            claims.get('sync_user'), claims.get('sync_fullname')
            # claims.get('ip_address')  # TODO for notification
        )
        user.update_fullname(claims.get('sync_fullname'))

        computer.sync_attributes.clear()

        # features
        for prefix, value in iteritems(claims.get('sync_attributes')):
            client_property = Property.objects.get(prefix=prefix)
            if client_property.sort == 'client':
                computer.sync_attributes.add(
                    *Attribute.process_kind_property(client_property, value)
                )

        # Domain attribute
        computer.sync_attributes.add(*Domain.process(computer.get_all_attributes()))

        # tags
        for tag in computer.tags.filter(property_att__enabled=True):
            Attribute.process_kind_property(tag.property_att, tag.value)

        # basic attributes
        computer.sync_attributes.add(
            *BasicAttribute.process(
                id=computer.id,
                ip_address=claims.get('ip_address'),
                project=computer.project.name,
                platform=computer.project.platform.name,
                user=user.name,
                description=computer.get_cid_description()
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
            sync_start_date=datetime.now()
        )

        serializer = serializers.ComputerSerializer(
            computer, context={'request': request}
        )

        add_computer_message(computer, gettext('Sending attributes response...'))

        return Response(
            self.create_response(serializer.data),
            status=status.HTTP_201_CREATED
        )

    @action(methods=['post'], detail=False)
    def repositories(self, request, format=None):
        """
        claims = {'id': 1}

        Returns: [{"name": slug, "source_template": "template"}, ...]
        """
        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        add_computer_message(computer, gettext('Getting repositories...'))

        repos = Deployment.available_deployments(
            computer, computer.get_all_attributes()
        )

        ret = []
        for repo in repos:
            ret.append({
                'name': repo.slug,
                'source_template': repo.source_template()
            })

        add_computer_message(computer, gettext('Sending repositories...'))

        if ret:
            return Response(
                self.create_response(ret),
                status=status.HTTP_200_OK
            )

        return Response(
            self.create_response(
                gettext('There are not available repositories')
            ),
            status=status.HTTP_404_NOT_FOUND
        )

    @action(methods=['post'], detail=False, url_path='faults/definitions')
    def fault_definitions(self, request, format=None):
        """
        claims = {'id': 1}

        Returns: [
            {
                'name': 'xxx',
                'language': 'bash' | 'php' | 'python' | 'ruby' | 'perl',
                'code': 'xxxx'
            },
            ...
        ]
        """
        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        add_computer_message(computer, gettext('Getting fault definitions...'))

        results = models.FaultDefinition.enabled_for_attributes(
            computer.get_all_attributes()
        )
        definitions = []
        for item in results:
            definitions.append({
                'language': item.get_language_display(),
                'name': item.name,
                'code': item.code
            })

        add_computer_message(computer, gettext('Sending fault definitions...'))

        if definitions:
            return Response(
                self.create_response(definitions),  # FIXME not serialized!!!
                status=status.HTTP_200_OK
            )

        return Response(
            self.create_response('There are not fault definitions'),
            status=status.HTTP_404_NOT_FOUND
        )

    @action(methods=['post'], detail=False)
    def faults(self, request, format=None):
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

        add_computer_message(computer, gettext('Getting faults...'))

        ret = []
        for name, result in iteritems(claims.get('faults')):
            try:
                definition = models.FaultDefinition.objects.get(name=name)
            except ObjectDoesNotExist:
                continue

            if result != '':  # something went wrong
                obj = models.Fault.objects.create(computer, definition, result)
                serializer = serializers.FaultSerializer(obj)
                ret.append(serializer.data)

        add_computer_message(computer, gettext('Sending faults response...'))

        return Response(
            self.create_response(list(ret)),
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=False)
    def errors(self, request, format=None):
        """
        claims = {
            'id': 1,
            'description': 'could not connect to host'
        }
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))
        claims['computer'] = computer.id
        claims['project'] = self.project.id

        add_computer_message(computer, gettext('Getting errors...'))

        serializer = serializers.ErrorSafeWriteSerializer(data=claims)

        add_computer_message(computer, gettext('Sending errors response...'))

        if serializer.is_valid():
            serializer.save()
            return Response(
                self.create_response(serializer.data),
                status=status.HTTP_201_CREATED
            )

        return Response(
            self.create_response(serializer.errors),
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(methods=['post'], detail=False, url_path='packages/mandatory')
    def mandatory_pkgs(self, request, format=None):
        """
        claims = {'id': 1}

        Returns: {
            "install": ["one", "two"],
            "remove": ["three"]
        }
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        add_computer_message(
            computer,
            gettext('Getting mandatory packages...')
        )

        pkgs = Deployment.available_deployments(
            computer, computer.get_all_attributes()
        ).values_list('packages_to_install', 'packages_to_remove')

        add_computer_message(
            computer,
            gettext('Sending mandatory packages...')
        )

        if pkgs:
            install = []
            remove = []
            for install_item, remove_item in pkgs:
                if install_item:
                    install = [x for x in install_item.split('\n') if x]

                if remove_item:
                    remove = [x for x in remove_item.split('\n') if x]

            # policies
            policy_pkg_to_install, policy_pkg_to_remove = Policy.get_packages(computer)
            install.extend(policy_pkg_to_install)
            remove.extend(policy_pkg_to_remove)

            response = {
                'install': remove_duplicates_preserving_order(install),
                'remove': remove_duplicates_preserving_order(remove)
            }

            return Response(
                self.create_response(response),
                status=status.HTTP_200_OK
            )

        return Response(
            self.create_response(
                gettext('There are not available mandatory packages')
            ),
            status=status.HTTP_404_NOT_FOUND
        )

    @action(methods=['post'], detail=False, url_path='tags/assigned')
    def assigned_tags(self, request, format=None):
        """
        claims = {'id': 1}

        Returns: {
            "tags": ["PR1-value1", "PR2-value2"]
        }
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        add_computer_message(computer, gettext('Getting assigned tags...'))

        tags = computer.tags.all()
        response = list([tag.__str__() for tag in tags])

        add_computer_message(computer, gettext('Sending assigned tags...'))

        return Response(
            self.create_response(response),
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=False, url_path='tags/available')
    def available_tags(self, request, format=None):
        """
        claims = {'id': 1}

        Returns: [
            {
                "name": ["PR1-value1", "PR2-value2"]
            },
            {
                "name2": ["PR3-value3"]
            },
            ...
        ]
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        add_computer_message(computer, gettext('Getting available tags...'))

        available = {}

        # Computer tags
        for tag in computer.tags.all():
            # if tag is a domain, includes all domain's tags
            if tag.property_att.prefix == 'DMN':
                for tag_dmn in Domain.objects.get(name=tag.value.split('.')[0]).get_tags():
                    if tag_dmn.property_att.name not in available:
                        available[tag_dmn.property_att.name] = []
                    value = tag_dmn.__str__()
                    if value not in available[tag_dmn.property_att.name]:
                        available[tag_dmn.property_att.name].append(value)

        # Deployment tags
        for deploy in Deployment.objects.filter(
            project__id=computer.project.id
        ).filter(enabled=True):
            for tag in deploy.included_attributes.filter(
                property_att__sort='server'
            ).filter(property_att__enabled=True):
                if tag.property_att.name not in available.keys():
                    available[tag.property_att.name] = []

                value = tag.__str__()
                if value not in available[tag.property_att.name]:
                    available[tag.property_att.name].append(value)

        # Domain Tags
        for domain in Domain.objects.filter(
            Q(included_attributes__in=computer.sync_attributes.all()) &
            ~Q(excluded_attributes__in=computer.sync_attributes.all())
        ):
            for tag in domain.tags.all():
                if tag.property_att.name not in available:
                    available[tag.property_att.name] = []
                value = tag.__str__()
                if value not in available[tag.property_att.name]:
                    available[tag.property_att.name].append(value)

        add_computer_message(computer, gettext('Sending available tags...'))

        if not available:
            return Response(
                self.create_response(gettext('There are not available tags')),
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            self.create_response(available),
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=False)
    def tags(self, request, format=None):
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

        add_computer_message(computer, gettext('Getting tags...'))

        computer_tags_ids = computer.tags.values_list('id', flat=True)
        tags = claims.get('tags')
        tag_objs = Attribute.objects.filter_by_prefix_value(tags)
        if not tag_objs:
            return Response(
                self.create_response(gettext('Invalid tags')),
                status=status.HTTP_400_BAD_REQUEST
            )

        computer.tags = tag_objs
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
            'packages_to_install',
            'default_preincluded_packages',
            'default_included_packages'
        )
        for packages_to_install, default_preincluded_packages, \
                default_included_packages in pkgs:
            if packages_to_install:
                [remove.append(x) for x in packages_to_install.split('\n') if x]
            if default_preincluded_packages:
                [remove.append(x) for x in
                    default_preincluded_packages.split('\n') if x]
            if default_included_packages:
                [remove.append(x) for x in
                    default_included_packages.split('\n') if x]

        pkgs = old_deploys.values_list(
            'packages_to_remove', 'default_excluded_packages'
        )
        for packages_to_remove, default_excluded_packages in pkgs:
            if packages_to_remove:
                [install.append(x) for x in packages_to_remove.split('\n') if x]
            if default_excluded_packages:
                [install.append(x) for x in
                    default_excluded_packages.split('\n') if x]

        # New deploys
        new_deploys = Deployment.available_deployments(
            computer,
            new_tags + intersection_tags
        )
        pkgs = new_deploys.values_list(
            'packages_to_remove', 'default_excluded_packages'
        )
        for packages_to_remove, default_excluded_packages in pkgs:
            if packages_to_remove:
                [remove.append(x) for x in packages_to_remove.split('\n') if x]
            if default_excluded_packages:
                [remove.append(x) for x in
                    default_excluded_packages.split('\n') if x]

        pkgs = new_deploys.values_list(
            'packages_to_install', 'default_included_packages'
        )
        for packages_to_install, default_included_packages in pkgs:
            if packages_to_install:
                [install.append(x) for x in
                    packages_to_install.split('\n') if x]
            if default_included_packages:
                [install.append(x) for x in
                    default_included_packages.split('\n') if x]

        pkgs = new_deploys.values_list('default_preincluded_packages')
        for default_preincluded_packages in pkgs:
            if default_preincluded_packages:
                [preinstall.append(x) for x in
                    default_preincluded_packages.split('\n') if x]

        ret = {
            "preinstall": remove_duplicates_preserving_order(preinstall),
            "install": remove_duplicates_preserving_order(install),
            "remove": remove_duplicates_preserving_order(remove),
        }

        add_computer_message(computer, gettext('Sending tags...'))

        return Response(
            self.create_response(ret),
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=False)
    def label(self, request, format=None):
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

        return Response(
            self.create_response(ret),
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=False, url_path='hardware/required')
    def hardware_capture_is_required(self, request, format=None):
        """
        claims = {'id': 1}

        Returns: {
            "capture": true | false
        }
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        add_computer_message(
            computer, gettext('Getting hardware capture is required...')
        )

        capture = computer.hardware_capture_is_required()

        add_computer_message(
            computer, gettext('Sending hardware capture response...')
        )

        return Response(
            self.create_response({'capture': capture}),
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=False)
    def software(self, request, format=None):
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

        add_computer_message(computer, gettext('Getting software...'))

        if 'inventory' not in claims and 'history' not in claims:
            return Response(
                self.create_response(gettext('Bad request')),
                status=status.HTTP_400_BAD_REQUEST
            )

        computer.update_software_history(claims.get('history'))
        tasks.update_software_inventory.delay(
            computer.id, claims.get('inventory')
        )

        add_computer_message(computer, gettext('Sending software response...'))

        return Response(
            self.create_response(gettext('Data received')),
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=False)
    def devices(self, request, format=None):
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
                        "feature": "xxxx",
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

        logical_devices = []
        for device in computer.logical_devices():
            logical_devices.append(device.as_dict(computer.project))

        if computer.default_logical_device:
            default_logical_device = computer.default_logical_device.id
        else:
            default_logical_device = 0

        logger.debug('logical devices: %s', logical_devices)
        logger.debug('default logical device: %d', default_logical_device)

        response = {
            'logical': logical_devices,
            'default': default_logical_device,
        }

        return Response(
            self.create_response(response),
            status=status.HTTP_200_OK
        )
