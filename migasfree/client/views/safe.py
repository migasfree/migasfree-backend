# -*- coding: utf-8 *-*

# Copyright (c) 2015 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015 Alberto Gacías <alberto@migasfree.org>
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

from datetime import datetime, timedelta

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets, mixins, status, views
from rest_framework.decorators import list_route
from rest_framework.response import Response
from django_redis import get_redis_connection

from migasfree.utils import uuid_change_format, trans
from migasfree.model_update import update
from migasfree import secure
from migasfree.core.models import (
    Project, Repository, Property, Attribute, BasicAttribute
)

from .. import models, serializers, tasks

import logging
logger = logging.getLogger('migasfree')


def add_computer_message(computer, message):
    con = get_redis_connection('default')
    con.hmset(
        'migasfree:msg:%d' % computer.id, {
            'date': datetime.now(),
            'name': computer.__str__(),
            'project': computer.project.name,
            'ip': computer.ip_address,
            'user': computer.sync_user.fullname,
            'msg': message
        }
    )
    con.sadd('migasfree:watch:msg', computer.id)


def remove_computer_messages(id):
    con = get_redis_connection('default')
    con.hdel('migasfree:msg:%d' % id, '*')
    con.srem('migasfree:watch:msg', id)


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

    if settings.MIGASFREE_NOTIFY_CHANGE_NAME and (computer.name != name):
        msg = _("Computer id=[%s]: NAME [%s] changed by [%s]") % (
            computer.id,
            computer.__str__(),
            name
        )
        models.Notification.objects.create(message=msg)

    if settings.MIGASFREE_NOTIFY_CHANGE_IP and (computer.ip_address != ip_address):
        msg = _("Computer id=[%s]: IP [%s] changed by [%s]") % (
            computer.id,
            computer.ip_address,
            ip_address
        )
        models.Notification.objects.create(message=msg)

    if settings.MIGASFREE_NOTIFY_CHANGE_UUID and (computer.uuid != uuid):
        msg = _("Computer id=[%s]: UUID [%s] changed by [%s]") % (
            computer.id,
            computer.uuid,
            uuid
        )
        models.Notification.objects.create(message=msg)


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

    try:
        computer = models.Computer.objects.get(name=name)
        logger.debug('computer found by name')

        return computer
    except models.Computer.DoesNotExist, models.Computer.MultipleObjectsReturned:
        return None


class SafeConnectionMixin(object):
    project = None

    def get_claims(self, data):
        """
        Decrypt and verify data
        data = {
            'msg': jwt,
            'project': project_name
        }
        """
        msg = data.get('msg')
        self.project = get_object_or_404(
            Project, name=data.get('project')
        )
        claims = secure.unwrap(
            msg,
            decrypt_key=settings.MIGASFREE_PRIVATE_KEY,
            verify_key='%s.pub' % self.project.slug
        )
        logger.debug('get_claims: %s' % claims)
        return claims

    def create_response(self, data):
        """
        Sign and encrypt data
        Returns: {
            'msg': jwt
        }
        """
        if not self.project:
            raise ObjectDoesNotExist(_('No project to sign message'))

        logger.debug('create_response: %s' % data)
        msg = secure.wrap(data,
            sign_key=settings.MIGASFREE_PRIVATE_KEY,
            encrypt_key='%s.pri' % self.project.slug
        )

        return {'msg': msg}


class SafeSynchronizationView(SafeConnectionMixin, views.APIView):
    def post(self, request, format=None):
        """
        claims = {
            "id": id,
            "start_date": datetime,
            "consumer": string
        }
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        data = {
            'computer': computer.id,
            'user': computer.sync_user.id,
            'project': self.project.id,
            'start_date': claims.get('start_date'),
            'consumer': claims.get('consumer')
        }
        serializer = serializers.SynchronizationSerializer(data=data)
        if serializer.is_valid():
            synchronization = serializer.save()

            remove_computer_messages(computer.id)

            return Response(
                self.create_response(serializer.data),
                status=status.HTTP_201_CREATED
            )

        return Response(
            self.create_response(serializer.errors),
            status=status.HTTP_400_BAD_REQUEST
        )


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

        serializer = serializers.ComputerSerializer(data=claims)
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

    @list_route(methods=['post'])
    def id(self, request, format=None):
        """
        claims = {
            'uuid': '01020304050607080910111213141516',
            'name': 'PC12345'
        }
        Returns a computer ID (or 404 if not found)
        """

        claims = self.get_claims(request.data)

        if 'uuid' not in claims.keys() or 'name' not in claims.keys():
            return Response(
                self.create_response(trans('Malformed claims')),
                status=status.HTTP_400_BAD_REQUEST
            )

        computer = get_computer(claims['uuid'], claims['name'])
        if not computer:
            return Response(
                self.create_response(trans('Computer not found')),
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            self.create_response(computer.id),
            status=status.HTTP_200_OK
        )

    @list_route(methods=['post'])
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

        properties = Property.enabled_client_properties()
        if properties:
            return Response(
                self.create_response(properties),
                status=status.HTTP_200_OK
            )

        return Response(
            self.create_response('There are not properties'),
            status=status.HTTP_404_NOT_FOUND
        )

    @list_route(methods=['post'])
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

        computer.sync_attributes.clear()

        # features
        for key, value in claims.get('sync_attributes').iteritems():
            prop = Property.objects.get(prefix=key)
            for att_id in Attribute.process_kind_property(prop, value):
                computer.sync_attributes.add(att_id)

        # tags
        for tag in computer.tags.all().filter(property_att__enabled=True):
            Attribute.process_kind_property(tag.property_att, tag.value)

        # basic attributes
        att_id = BasicAttribute.process(
            id=computer.id,
            ip_address=claims.get('ip_address'),
            project=computer.project.name,
            platform=computer.project.platform.name,
            user=user.name
        )
        for id in att_id:
            computer.sync_attributes.add(id)

        update(computer,
            uuid=claims.get('uuid'),
            name=claims.get('name'),
            ip_address=claims.get('ip_address'),
            sync_user=user,
            sync_start_date=datetime.now()
        )

        serializer = serializers.ComputerSerializer(computer)

        return Response(
            self.create_response(serializer.data),
            status=status.HTTP_201_CREATED
        )

    @list_route(methods=['post'])
    def repositories(self, request, format=None):
        """
        claims = {'id': 1}

        Returns: [
            slug,
            ...
        ]
        """
        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        add_computer_message(computer, trans('Getting repositories...'))

        repos = Repository.available_repos(
            computer.project.id, computer.get_all_attributes()
        ).values_list('slug', flat=True)

        add_computer_message(computer, trans('Sending repositories...'))

        if repos:
            return Response(
                self.create_response(list(repos)),
                status=status.HTTP_200_OK
            )

        return Response(
            self.create_response(trans('There are not available repositories')),
            status=status.HTTP_404_NOT_FOUND
        )

    @list_route(methods=['post'], url_path='faults/definitions')
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

        add_computer_message(computer, trans('Getting fault definitions...'))

        definitions = models.FaultDefinition.enabled_for_attributes(
            computer.get_all_attributes()
        )

        add_computer_message(computer, trans('Sending fault definitions...'))

        if definitions:
            return Response(
                self.create_response(definitions),  # FIXME not serialized!!!
                status=status.HTTP_200_OK
            )

        return Response(
            self.create_response('There are not fault definitions'),
            status=status.HTTP_404_NOT_FOUND
        )

    @list_route(methods=['post'])
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

        add_computer_message(computer, trans('Getting faults...'))

        ret = []
        for name, result in claims.get('faults').iteritems():
            try:
                definition = models.FaultDefinition.objects.get(name=name)
            except:
                continue

            if result != '':  # something went wrong
                obj = models.Fault.objects.create(computer, definition, result)
                serializer = serializers.FaultSerializer(obj)
                ret.append(serializer.data)

        add_computer_message(computer, trans('Sending faults response...'))

        return Response(
            self.create_response(list(ret)),
            status=status.HTTP_200_OK
        )

    @list_route(methods=['post'])
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

        add_computer_message(computer, trans('Getting errors...'))

        serializer = serializers.ErrorSerializer(data=claims)

        add_computer_message(computer, trans('Sending errors response...'))

        if serializer.is_valid():
            error = serializer.save()
            return Response(
                self.create_response(serializer.data),
                status=status.HTTP_201_CREATED
            )

        return Response(
            self.create_response(serializer.errors),
            status=status.HTTP_400_BAD_REQUEST
        )

    @list_route(methods=['post'], url_path='packages/mandatory')
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

        pkgs = Repository.available_repos(
            computer.project.id, computer.get_all_attributes()
        ).values_list('packages_to_install', 'packages_to_remove')

        if pkgs:
            install = []
            remove = []
            for install_item, remove_item in pkgs:
                if install_item:
                    [install.append(x) for x in install_item.split('\n') if x]

                if remove_item:
                    [remove.append(x) for x in remove_item.split('\n') if x]

            response = {'install': install, 'remove': remove}

            return Response(
                self.create_response(response),
                status=status.HTTP_200_OK
            )

        return Response(
            self.create_response(
                trans('There are not available mandatory packages')
            ),
            status=status.HTTP_404_NOT_FOUND
        )

    @list_route(methods=['post'], url_path='tags/assigned')
    def assigned_tags(self, request, format=None):
        """
        claims = {'id': 1}

        Returns: {
            "tags": ["PR1-value1", "PR2-value2"]
        }
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))
        tags = computer.tags.all()
        """
        response = {
            'tags': [tag.__str__() for tag in tags]
        }
        """
        response = list([tag.__str__() for tag in tags])

        return Response(
            self.create_response(response),
            status=status.HTTP_200_OK
        )

    @list_route(methods=['post'], url_path='tags/available')
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

        available = {}
        for repos in Repository.objects.filter(
            project__id=computer.project.id
        ).filter(enabled=True):
            for tag in repos.included_attributes.filter(
                property_att__sort='server'
            ).filter(property_att__enabled=True):
                if tag.property_att.name not in available.keys():
                    available[tag.property_att.name] = []

                value = tag.__str__()
                if value not in available[tag.property_att.name]:
                    available[tag.property_att.name].append(value)

        if not available:
            return Response(
                self.create_response(trans('There are not available tags')),
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            self.create_response(available),
            status=status.HTTP_200_OK
        )

    @list_route(methods=['post'])
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

        computer_tags_ids = computer.tags.all().values_list('id', flat=True)
        tags = claims.get('tags')
        tag_objs = Attribute.objects.filter_by_prefix_value(tags)
        if not tag_objs:
            return Response(
                self.create_response(trans('Invalid tags')),
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            computer.tags = tag_objs
        except:
            computer.tags.clear()

        tag_ids = tag_objs.values_list('id', flat=True)

        old_tags = list(set(computer_tags_ids) - set(tag_ids))
        new_tags = list(set(tag_ids) - set(computer_tags_ids))
        intersection_tags = list(set(computer_tags_ids).intersection(tag_ids))

        preinstall = []
        install = []
        remove = []

        # Old Repositories
        repos = Repository.available_repos(
            computer.project.id, old_tags
        )
        pkgs = repos.values_list(
            'packages_to_install',
            'default_preincluded_packages',
            'default_included_packages'
        )
        for packages_to_install, default_preincluded_packages, \
        default_included_packages in pkgs:
            if packages_to_install:
                [remove.append(x) for x in packages_to_install.split('\n') if x]
            if default_preincluded_packages:
                [remove.append(x) for x in \
                default_preincluded_packages.split('\n') if x]
            if default_included_packages:
                [remove.append(x) for x in \
                default_included_packages.split('\n') if x]

        pkgs = repos.values_list(
            'packages_to_remove', 'default_excluded_packages'
        )
        for packages_to_remove, default_excluded_packages in pkgs:
            if packages_to_remove:
                [install.append(x) for x in packages_to_remove.split('\n') if x]
            if default_excluded_packages:
                [install.append(x) for x in \
                default_excluded_packages.split('\n') if x]

        # New Repositories
        repos = Repository.available_repos(
            computer.project.id,
            new_tags + intersection_tags
        )
        pkgs = repos.values_list(
            'packages_to_remove', 'default_excluded_packages'
        )
        for packages_to_remove, default_excluded_packages in pkgs:
            if packages_to_remove:
                [remove.append(x) for x in packages_to_remove.split('\n') if x]
            if default_excluded_packages:
                [remove.append(x) for x in \
                default_excluded_packages.split('\n') if x]

        pkgs = repos.values_list(
            'packages_to_install', 'default_included_packages'
        )
        for packages_to_install, default_included_packages in pkgs:
            if packages_to_install:
                [install.append(x) for x in \
                packages_to_install.split('\n') if x]
            if default_included_packages:
                [install.append(x) for x in \
                default_included_packages.split('\n') if x]

        pkgs = repos.values_list('default_preincluded_packages')
        for default_preincluded_packages in pkgs:
            if default_preincluded_packages:
                [preinstall.append(x) for x in \
                default_preincluded_packages.split('\n') if x]

        ret = {
            "preinstall": preinstall,
            "install": install,
            "remove": remove,
        }

        return Response(
            self.create_response(ret),
            status=status.HTTP_200_OK
        )

    @list_route(methods=['post'])
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

        ret = {
            'uuid': computer.uuid,
            'name': computer.name,
            'search': computer.__str__(),
            'helpdesk': settings.MIGASFREE_HELP_DESK,
        }

        return Response(
            self.create_response(ret),
            status=status.HTTP_200_OK
        )

    @list_route(methods=['post'], url_path='hardware/required')
    def hardware_capture_is_required(self, request, format=None):
        """
        claims = {'id': 1}

        Returns: {
            "capture": true | false
        }
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        if computer.last_hardware_capture:
            capture = (datetime.now() > (
                computer.last_hardware_capture + timedelta(
                    days=settings.MIGASFREE_HW_PERIOD
                ))
            )
        else:
            capture = True

        return Response(
            self.create_response({'capture': capture}),
            status=status.HTTP_200_OK
        )

    @list_route(methods=['post'])
    def software(self, request, format=None):
        """
        claims = {
            'id', 1,
            'inventory': ['asdasd', 'asdasdsd', 'asdasdsd', ...],
            'history': 'asdadf\n\dfasdfaf'
        }
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))

        add_computer_message(computer, trans('Getting software...'))

        if 'inventory' not in claims and 'history' not in claims:
            return Response(
                self.create_response(trans('Bad request')),
                status=status.HTTP_400_BAD_REQUEST
            )

        computer.update_software_history(claims.get('history'))
        tasks.update_software_inventory.delay(
            computer.id, claims.get('inventory')
        )

        add_computer_message(computer, trans('Sending software response...'))

        return Response(
            self.create_response(trans('Data received')),
            status=status.HTTP_200_OK
        )

    @list_route(methods=['post'])
    def devices(self, request, format=None):
        """
        claims = {'id': 1}

        Returns: {
            "install": ["one", "two"],
            "remove": ["three"]
        }
        """

        claims = self.get_claims(request.data)
        computer = get_object_or_404(models.Computer, id=claims.get('id'))
        # TODO to devices app views.py
