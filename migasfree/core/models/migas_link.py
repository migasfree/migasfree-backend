# -*- coding: utf-8 -*-

# Copyright (c) 2020-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2020-2021 Alberto Gacías <alberto@migasfree.org>
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

import json

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext

from ...utils import escape_format_string


class MigasLink(object):
    PROTOCOL = 'mea'

    ROUTES = {
        'auth.group': 'groups',
        'app_catalog.application': 'catalog/applications',
        'app_catalog.packagesbyproject': 'catalog/project-packages',
        'app_catalog.policy': 'catalog/policies',
        'app_catalog.policygroup': 'catalog/policy-groups',
        'client.computer': 'computers',
        'client.error': 'errors',
        'client.faultdefinition': 'fault-definitions',
        'client.fault': 'faults',
        'client.migration': 'migrations',
        'client.packagehistory': 'packages-history',
        'client.statuslog': 'status-logs',
        'client.synchronization': 'synchronizations',
        'client.user': 'users',
        'core.attribute': 'attributes',
        'core.clientattribute': 'attributes',
        'core.serverattribute': 'tags',
        'core.attributeset': 'attribute-sets',
        'core.domain': 'domains',
        'core.deployment': 'deployments',
        'core.packageset': 'package-sets',
        'core.package': 'packages',
        'core.platform': 'platforms',
        'core.project': 'projects',
        'core.clientproperty': 'formulas',
        'core.serverproperty': 'stamps',
        'core.scheduledelay': 'schedule-delays',
        'core.schedule': 'schedules',
        'core.scope': 'scopes',
        'core.store': 'stores',
        'core.userprofile': 'user-profiles',
        'device.capability': 'devices/capabilities',
        'device.connection': 'devices/connections',
        'device.device': 'devices/devices',
        'device.driver': 'devices/drivers',
        'device.logical': 'devices/logical',
        'device.manufacturer': 'devices/manufacturers',
        'device.model': 'devices/models',
        'device.type': 'devices/types',
    }

    def __init__(self):
        self._actions = None
        self._exclude_links = []
        self._include_links = []

    def model_to_route(self, app, model):
        return self.ROUTES.get('{}.{}'.format(app, model), '')

    @staticmethod
    def related_title(related_objects):
        if not related_objects:
            return ''

        first = related_objects[0]

        return first._meta.verbose_name if related_objects.count() == 1 else first._meta.verbose_name_plural

    @staticmethod
    def get_description(action):
        return action.get('description', '')

    def is_related(self, action):
        model = self._meta.model_name.lower()

        if 'related' in action:
            # COMPUTER === CID ATTRIBUTE
            if self._meta.model_name == 'computer' or (
                (
                    self._meta.model_name in ['attribute', 'clientattribute']
                ) and self.property_att.prefix == 'CID'
            ):
                model = 'computer'

            # ATTRIBUTE SET === ATTRIBUTE
            elif self._meta.model_name == 'attributeset' \
                    or (self._meta.model_name == 'attribute' and self.pk > 1) \
                    and self.property_att.prefix == 'SET':
                model = 'attributeset'

            # DOMAIN === ATTRIBUTE
            elif self._meta.model_name == 'domain' or \
                    (self._meta.model_name in ['attribute', 'serverattribute'] and self.property_att.prefix == 'DMN'):
                model = 'domain'

        return 'related' not in action or model in action['related']

    def get_relations(self, request):
        user = request.user.userprofile
        server = request.META.get('HTTP_HOST')

        related_objects = [
            (f, f.model if f.model != self else None)
            for f in self._meta.get_fields()
            if (f.one_to_many or f.one_to_one)
            and f.auto_created and not f.concrete
        ] + [
            (f, f.model if f.model != self else None)
            for f in self._meta.get_fields(include_hidden=True)
            if f.many_to_many and f.auto_created
        ]

        objs = [
            (f, f.model if f.model != self else None)
            for f in self._meta.get_fields()
            if f.many_to_many and not f.auto_created
        ]

        actions = []
        data = []
        if self._actions is not None and any(self._actions):
            for item in self._actions:
                actions.append({
                    'url': item[1],
                    'title': item[0],
                    'description': item[2] if len(item) == 3 else '',
                })

        if self._meta.model_name.lower() in settings.MIGASFREE_EXTERNAL_ACTIONS:
            element = settings.MIGASFREE_EXTERNAL_ACTIONS[self._meta.model_name.lower()]
            for action in element:
                if self.is_related(element[action]):
                    action_info = {
                        'name': action,
                        'model': self._meta.model_name,
                        'id': self.id,
                        'related_model': self._meta.model_name,
                        'related_ids': [self.id],
                        'server': server
                    }

                    actions.append({
                        'url': '{}://{}'.format(self.PROTOCOL, json.dumps(action_info)),
                        'title': element[action]['title'],
                        'description': self.get_description(element[action]),
                    })

        data.append({
            'model': self.model_to_route(self._meta.app_label, self._meta.model_name),
            'pk': self.id,
            'text': '{} {}'.format(self._meta.verbose_name, self.__str__()),
            'count': 1,
            'actions': actions
        })

        for obj, _ in objs:
            if obj.remote_field.field.remote_field.parent_link:
                _name = obj.remote_field.field.remote_field.parent_model.__name__.lower()
            else:
                _name = obj.remote_field.field.remote_field.model.__name__.lower()

            if _name == 'attribute':
                if self._meta.model_name == 'computer' and obj.attname == 'tags':
                    _name = 'tag'

            if _name == 'permission':
                break

            if hasattr(obj.remote_field.model.objects, 'scope'):
                rel_objects = obj.remote_field.model.objects.scope(user).filter(
                    **{obj.remote_field.name: self.id}
                )
            else:
                rel_objects = obj.remote_field.model.objects.filter(
                    **{obj.remote_field.name: self.id}
                )
            count = rel_objects.count()

            if count:
                actions = []
                if _name in settings.MIGASFREE_EXTERNAL_ACTIONS:
                    element = settings.MIGASFREE_EXTERNAL_ACTIONS[_name]
                    for action in element:
                        if 'many' not in element[action] or element[action]['many'] or count == 1:
                            if self.is_related(element[action]):
                                info_action = {
                                    'name': action,
                                    'model': self._meta.model_name,
                                    'id': self.id,
                                    'related_model': _name,
                                    'related_ids': list(rel_objects.values_list('id', flat=True)),
                                    'server': server,
                                }

                                actions.append({
                                    'url': '{}://{}'.format(self.PROTOCOL, json.dumps(info_action)),
                                    'title': element[action]['title'],
                                    'description': self.get_description(element[action]),
                                })

                data.append({
                    'api': {
                        'model': self.model_to_route(
                            obj.remote_field.model._meta.app_label,
                            obj.remote_field.model._meta.model_name
                        ),
                        'query': {
                            '{}__id'.format(obj.remote_field.name): self.pk
                        }
                    },
                    'text': gettext(obj.remote_field.field.verbose_name),
                    'count': count,
                    'actions': actions
                })

        for related_object, _ in related_objects:
            related_model, _field = self.transmodel(related_object)
            if related_model:
                # EXCLUDE CID
                if related_model.__name__.lower() != 'computer' or not (
                        self._meta.model_name == 'attribute' and self.property_att.prefix == 'CID'
                ):
                    if not '{} - {}'.format(
                        related_model._meta.model_name,
                        _field
                    ) in self._exclude_links:
                        if hasattr(related_model.objects, 'scope'):
                            if related_model.__name__.lower() == 'computer':
                                rel_objects = related_model.productive.scope(user).filter(
                                    **{related_object.field.name: self.id}
                                )
                            else:
                                rel_objects = related_model.objects.scope(user).filter(
                                    **{related_object.field.name: self.id}
                                )
                        else:
                            rel_objects = related_model.objects.filter(
                                **{related_object.field.name: self.id}
                            )

                        count = rel_objects.count()
                        if count and related_model._meta.app_label != 'authtoken':
                            actions = []
                            if related_model.__name__.lower() in settings.MIGASFREE_EXTERNAL_ACTIONS:
                                element = settings.MIGASFREE_EXTERNAL_ACTIONS[related_model.__name__.lower()]
                                for action in element:
                                    if 'many' not in element[action] or element[action]['many'] or count == 1:
                                        if self.is_related(element[action]):
                                            info_action = {
                                                'name': action,
                                                'model': self._meta.model_name,
                                                'id': self.id,
                                                'related_model': related_model.__name__.lower(),
                                                'related_ids': list(rel_objects.values_list('id', flat=True)),
                                                'server': server,
                                            }

                                            actions.append({
                                                'url': '{}://{}'.format(self.PROTOCOL, json.dumps(info_action)),
                                                'title': element[action]['title'],
                                                'description': self.get_description(element[action]),
                                            })

                            if related_model.__name__.lower() == 'computer':
                                data.append({
                                    'api': {
                                        'model': self.model_to_route(
                                            related_model._meta.app_label,
                                            related_model._meta.model_name
                                        ),
                                        'query': {
                                            _field: self.id,
                                            'status__in': 'intended,reserved,unknown'
                                        }
                                    },
                                    'text': '{} [{}]'.format(
                                        gettext(related_model._meta.verbose_name_plural),
                                        gettext(related_object.field.verbose_name)
                                    ),
                                    'count': count,
                                    'actions': actions
                                })
                            else:
                                if related_model.__name__.lower() == 'faultdefinition' \
                                        and _field == 'users__user_ptr':
                                    _field = 'users__id'

                                data.append({
                                    'api': {
                                        'model': self.model_to_route(
                                            related_model._meta.app_label,
                                            related_model._meta.model_name
                                        ),
                                        'query': {
                                            _field: self.id
                                        }
                                    },
                                    'text': '{} [{}]'.format(
                                        gettext(related_model._meta.verbose_name_plural),
                                        gettext(related_object.field.verbose_name)
                                    ),
                                    'count': count,
                                    'actions': actions
                                })

        # SPECIAL RELATIONS (model must have a method named: 'related_objects').
        actions = []
        if self._meta.model_name.lower() in [
            'device', 'deployment', 'scope', 'domain',
            'attributeset', 'faultdefinition', 'platform'
        ]:
            rel_objects = self.related_objects('computer', user)
            if rel_objects.exists():
                if 'computer' in settings.MIGASFREE_EXTERNAL_ACTIONS:
                    element = settings.MIGASFREE_EXTERNAL_ACTIONS['computer']
                    for action in element:
                        if 'many' not in element[action] or element[action]['many'] or rel_objects.count() == 1:
                            if self.is_related(element[action]):
                                info_action = {
                                    'name': action,
                                    'model': self._meta.model_name,
                                    'id': self.id,
                                    'related_model': 'computer',
                                    'related_ids': list(rel_objects.values_list('id', flat=True)),
                                    'server': server,
                                }

                                actions.append({
                                    'url': '{}://{}'.format(self.PROTOCOL, json.dumps(info_action)),
                                    'title': element[action]['title'],
                                    'description': self.get_description(element[action]),
                                })

                    if self._meta.model_name.lower() == 'platform':
                        from ...client.models.computer import Computer
                        data.append({
                            'api': {
                                'model': 'computers',
                                'query': {
                                    'platform__id': self.id,
                                    'status__in': ','.join(Computer.PRODUCTIVE_STATUS)
                                }
                            },
                            'text': gettext(self.related_title(rel_objects)),
                            'count': rel_objects.count(),
                            'actions': actions
                        })
                    elif self._meta.model_name.lower() == 'device':
                        from .attribute import Attribute
                        data.append({
                            'api': {
                                'model': 'computers',
                                'query': {
                                    'sync_attributes__id__in': ','.join(map(str, list(
                                        Attribute.objects.scope(
                                            request.user.userprofile
                                        ).filter(
                                            logical__device__id=self.id
                                        ).values_list('id', flat=True)))
                                    ),
                                    'status__in': 'intended,reserved,unknown'
                                }
                            },
                            'text': gettext(self.related_title(rel_objects)),
                            'count': rel_objects.count(),
                            'actions': actions
                        })
                    else:
                        data.append({
                            'api': {
                                'model': 'computers',
                                'query': {
                                    'id__in': ','.join(map(str, list(rel_objects.values_list('id', flat=True))))
                                }
                            },
                            'text': gettext(self.related_title(rel_objects)),
                            'count': rel_objects.count(),
                            'actions': actions
                        })

        if self._meta.model_name.lower() == 'computer':
            # special case installed packages
            installed_packages_count = self.packagehistory_set.filter(
                package__project=self.project,
                uninstall_date__isnull=True
            ).count()
            if installed_packages_count > 0:
                data.append({
                    'api': {
                        'model': self.model_to_route('client', 'packagehistory'),
                        'query': {
                            'computer__id': self.id,
                            'package__project__id': self.project.id,
                            'uninstall_date': True  # isnull = True
                        },
                    },
                    'text': '{} [{}]'.format(
                        gettext('Installed Packages'),
                        gettext('computer')
                    ),
                    'count': installed_packages_count,
                    'actions': actions
                })

        if self._meta.model_name.lower() == 'package':
            # special case computers with package installed
            computers_count = self.packagehistory_set.filter(
                package=self,
                uninstall_date__isnull=True
            ).count()
            if computers_count > 0:
                data.append({
                    'api': {
                        'model': self.model_to_route('client', 'computer'),
                        'query': {
                            'installed_package': self.id
                        },
                    },
                    'text': '{} [{}]'.format(
                        gettext('Installed package'),
                        gettext('computer')
                    ),
                    'count': computers_count,
                    'actions': actions
                })

        for _include in self._include_links:
            try:
                _model_name, _field_name = _include.split(' - ')
                data.append({
                    'api': {
                        'model': self.model_to_route(
                            self._meta.app_label,
                            _model_name
                        ),
                        'query': {
                            '{}__id'.format(_field_name): self.id
                        }
                    },
                    'text': '{} [{}]'.format(
                        gettext(_model_name),
                        gettext(_field_name)
                    )
                })
            except ValueError:
                pass

        return data

    def relations(self, request):
        data = []

        if self._meta.model_name == 'node':
            from ...client.models import Computer
            data.append({
                'api': {
                    'model': 'computers',
                    'query': {'product': self.computer.product},
                },
                'text': '{} [{}]'.format(
                    gettext('computer'),
                    gettext('product')
                ),
                'count': Computer.productive.scope(request.user.userprofile).filter(
                    product=self.computer.product
                ).count(),
                'actions': []
            })

            return data

        # DOMAIN === ATTRIBUTE
        if self._meta.model_name == 'domain' or (
                self._meta.model_name == 'serverattribute' and self.property_att.prefix == 'DMN'
        ):
            if self._meta.model_name == 'domain':
                from . import ServerAttribute
                domain = self
                try:
                    att = ServerAttribute.objects.get(
                        value=str(self.name),
                        property_att__prefix='DMN'
                    )
                except ObjectDoesNotExist:
                    att = None
            else:
                from . import Domain
                att = self
                try:
                    domain = Domain.objects.get(name=self.value)
                except ObjectDoesNotExist:
                    domain = None
            if att:
                att_data = att.get_relations(request)
            else:
                att_data = []

            if domain:
                set_data = domain.get_relations(request)
                data = set_data + att_data

            return data

        # ATTRIBUTE SET === ATTRIBUTE
        if self._meta.model_name == 'attributeset' \
                or (self._meta.model_name == 'attribute' and self.pk > 1) \
                and self.property_att.prefix == 'SET':
            if self._meta.model_name == 'attributeset':
                from . import Attribute
                attribute_set = self
                try:
                    att = Attribute.objects.get(
                        value=str(self.name),
                        property_att__prefix='SET'
                    )
                except ObjectDoesNotExist:
                    att = None
            else:
                from . import AttributeSet
                att = self
                try:
                    attribute_set = AttributeSet.objects.get(name=self.value)
                except ObjectDoesNotExist:
                    attribute_set = None

            if att:
                att_data = att.get_relations(request)
            else:
                att_data = []

            if attribute_set:
                set_data = attribute_set.get_relations(request)
                data = set_data + att_data

            return data

        # COMPUTER === CID ATTRIBUTE
        if self._meta.model_name == 'computer' or (
                (
                    self._meta.model_name == 'attribute' or
                    self._meta.model_name == 'clientattribute'
                ) and self.property_att.prefix == 'CID'
        ):
            if self._meta.model_name == 'computer':
                from . import Attribute
                computer = self
                try:
                    cid = Attribute.objects.get(
                        value=str(self.id),
                        property_att__prefix='CID'
                    )
                except ObjectDoesNotExist:
                    cid = None
            else:
                from ...client.models import Computer
                cid = self
                computer = Computer.objects.get(pk=int(self.value))

            computer_data = computer.get_relations(request)

            if cid:
                cid_data = cid.get_relations(request)
            else:
                cid_data = []

            data = computer_data + cid_data

            return data
        else:
            return self.get_relations(request)

    def badge(self):
        if self._meta.model_name == 'clientattribute' \
                or self._meta.model_name == 'attribute':
            if self.property_att.prefix == 'CID':
                from ...client.models import Computer
                try:
                    self = Computer.objects.get(id=self.value)
                except ObjectDoesNotExist:
                    pass
            elif self.property_att.prefix == 'SET':
                from . import AttributeSet
                try:
                    self = AttributeSet.objects.get(name=self.value)
                except ObjectDoesNotExist:
                    pass
            elif self.property_att.prefix == 'DMN':
                from . import Domain
                try:
                    self = Domain.objects.get(name=self.value)
                except ObjectDoesNotExist:
                    pass

        lnk = {
            'pk': self.id,
            'text': escape_format_string(self.__str__()),
        }
        if self._meta.model_name == 'computer':
            lnk['status'] = self.status
            lnk['summary'] = '{}, {}, {}, {}'.format(
                gettext(self.status),
                self.project,
                self.ip_address,
                self.sync_user
            )
        elif self._meta.model_name == 'domain':
            lnk['status'] = 'domain'
            lnk['summary'] = gettext(self._meta.verbose_name)
        elif self._meta.model_name == 'serverattribute' \
                or (self._meta.model_name == 'attribute' and self.property_att.sort == 'server'):
            lnk['status'] = 'tag'
            lnk['summary'] = gettext(self._meta.verbose_name)
        elif self._meta.model_name == 'attributeset' \
                or (self._meta.model_name in ['clientattribute', 'attribute'] and self.id == 1):
            lnk['status'] = 'set'
            lnk['summary'] = '({}) {}'.format(gettext(self._meta.verbose_name), self.description)
        elif self._meta.model_name == 'clientattribute' \
                or (self._meta.model_name == 'attribute' and self.property_att.sort == 'client'):
            lnk['status'] = 'attribute'
            lnk['summary'] = self.description
        elif self._meta.model_name == 'policy':
            lnk['status'] = 'policy'
            lnk['summary'] = gettext(self._meta.verbose_name)

        return lnk

    def transmodel(self, obj):
        from ...client.models import Computer
        from . import ClientAttribute, ServerAttribute

        if obj.related_model._meta.label_lower == 'client.computer' and \
                self.__class__.__name__ in ['ClientAttribute', 'Attribute'] and \
                self.property_att.prefix == 'CID':
            return Computer, 'sync_attributes__id'

        if obj.related_model._meta.label_lower == 'core.attribute':
            if self.sort == 'server':
                return ServerAttribute, 'property__id'
            else:
                return ClientAttribute, 'property__id'
        elif obj.related_model._meta.label_lower == 'client.computer':
            if self.__class__.__name__ == ['ClientAttribute', 'Attribute', 'ServerAttribute']:
                if obj.field.related_model._meta.model_name == 'serverattribute':
                    return Computer, 'tags__id'
                elif obj.field.related_model._meta.model_name == 'attribute':
                    return Computer, 'sync_attributes__id'
        elif obj.related_model._meta.label_lower in [
            'admin.logentry',
            'core.scheduledelay',
            'hardware.node'
        ]:
            return '', ''  # Excluded

        if obj.field.__class__.__name__ in ['ManyRelatedManager', 'OneToOneField', 'ForeignKey']:
            return obj.related_model, '{}__id'.format(obj.field.name)
        else:
            return obj.related_model, '{}__{}'.format(
                obj.field.name,
                obj.field.m2m_reverse_target_field_name()
            )
