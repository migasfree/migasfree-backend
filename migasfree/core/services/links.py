# Copyright (c) 2020-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2020-2026 Alberto Gacías <alberto@migasfree.org>
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

import base64
import json

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext

from ...utils import escape_format_string


class MigasLinkService:
    def __init__(self, instance):
        self._actions = instance._actions if hasattr(instance, '_actions') else None
        self._exclude_links = instance._exclude_links if hasattr(instance, '_exclude_links') else []
        self._include_links = instance._include_links if hasattr(instance, '_include_links') else []
        self.instance = instance
    PROTOCOL = 'mea'

    ROUTES = {
        'auth.group': 'groups',
        'app_catalog.application': 'catalog/applications',
        'app_catalog.category': 'catalog/categories',
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
        'core.clientattribute': 'features',
        'core.serverattribute': 'tags',
        'core.attributeset': 'attribute-sets',
        'core.domain': 'domains',
        'core.deployment': 'deployments',
        'core.packageset': 'package-sets',
        'core.package': 'packages',
        'core.platform': 'platforms',
        'core.project': 'projects',
        'core.property': 'formulas',
        'core.clientproperty': 'formulas',
        'core.serverproperty': 'stamps',
        'core.scheduledelay': 'schedule-delays',
        'core.schedule': 'schedules',
        'core.singularity': 'singularities',
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


    def custom_protocol(self, info_action):
        return f'{self.PROTOCOL}://{base64.urlsafe_b64encode(json.dumps(info_action).encode()).decode()}'

    def model_to_route(self, app, model):
        return self.ROUTES.get(f'{app}.{model}', '')

    @staticmethod
    def related_title(related_objects):
        if not related_objects:
            return ''

        first = related_objects[0]

        return first._meta.verbose_name if related_objects.count() == 1 else first._meta.verbose_name_plural

    @staticmethod
    def get_description(action):
        return action.get('description', '')

    def _build_external_actions(self, element_name, rel_ids, server, count):
        """Build external actions list for a given element."""
        actions = []
        if element_name not in settings.MIGASFREE_EXTERNAL_ACTIONS:
            return actions

        element = settings.MIGASFREE_EXTERNAL_ACTIONS[element_name]
        for action in element:
            action_cfg = element[action]
            allows_many = action_cfg.get('many', True)
            if (allows_many or count == 1) and self.is_related(action_cfg):
                info_action = {
                    'name': action,
                    'model': self.instance._meta.model_name,
                    'id': self.instance.id,
                    'related_model': element_name,
                    'related_ids': rel_ids,
                    'server': server,
                }
                actions.append(
                    {
                        'url': self.custom_protocol(info_action),
                        'title': action_cfg['title'],
                        'description': self.get_description(action_cfg),
                    }
                )

        return actions

    def is_related(self, action):
        model = self.instance._meta.model_name.lower()

        if 'related' in action:
            # COMPUTER === CID ATTRIBUTE
            if self.instance._meta.model_name == 'computer' or (
                (self.instance._meta.model_name in ['attribute', 'clientattribute']) and self.instance.property_att.prefix == 'CID'
            ):
                model = 'computer'

            # ATTRIBUTE SET === ATTRIBUTE
            elif self.instance._meta.model_name == 'attributeset' or (
                (self.instance._meta.model_name == 'attribute' and self.instance.pk > 1) and self.instance.property_att.prefix == 'SET'
            ):
                model = 'attributeset'

            # DOMAIN === ATTRIBUTE
            elif self.instance._meta.model_name == 'domain' or (
                self.instance._meta.model_name in ['attribute', 'serverattribute'] and self.instance.property_att.prefix == 'DMN'
            ):
                model = 'domain'

        return 'related' not in action or model in action['related']

    def _get_self_actions(self, server):
        """Get actions for the current model instance."""
        actions = []
        data = []

        if self._actions is not None and any(self._actions):
            for item in self._actions:
                actions.append(
                    {
                        'url': item[1],
                        'title': item[0],
                        'description': item[2] if len(item) == 3 else '',
                    }
                )

        if self.instance._meta.model_name.lower() in settings.MIGASFREE_EXTERNAL_ACTIONS:
            element = settings.MIGASFREE_EXTERNAL_ACTIONS[self.instance._meta.model_name.lower()]
            for action in element:
                if self.is_related(element[action]):
                    info_action = {
                        'name': action,
                        'model': self.instance._meta.model_name,
                        'id': self.instance.id,
                        'related_model': self.instance._meta.model_name,
                        'related_ids': [self.instance.id],
                        'server': server,
                    }

                    actions.append(
                        {
                            'url': self.custom_protocol(info_action),
                            'title': element[action]['title'],
                            'description': self.get_description(element[action]),
                        }
                    )

        if actions:
            data.append(
                {
                    'model': self.model_to_route(self.instance._meta.app_label, self.instance._meta.model_name),
                    'pk': self.instance.id,
                    'text': f'{self.instance._meta.verbose_name} {self.instance.__str__()}',
                    'count': 1,
                    'actions': actions,
                }
            )

        return data

    def _get_m2m_relations(self, user, server, objs):
        """Get many-to-many forward relations."""
        data = []

        for obj, _ in objs:
            if obj.remote_field.field.remote_field.parent_link:
                _name = obj.remote_field.field.remote_field.parent_model.__name__.lower()
            else:
                _name = obj.remote_field.field.remote_field.model.__name__.lower()

            if _name == 'attribute' and self.instance._meta.model_name == 'computer' and obj.attname == 'tags':
                _name = 'tag'

            if _name == 'permission':
                break

            if (
                _name == 'property'
                and self.instance._meta.model_name in ['serverattribute', 'attribute']
                and obj.attname == 'property_att_id'
            ):
                break

            if hasattr(obj.remote_field.model.objects, 'scope'):
                rel_objects = obj.remote_field.model.objects.scope(user).filter(**{obj.remote_field.name: self.instance.id})
            else:
                rel_objects = obj.remote_field.model.objects.filter(**{obj.remote_field.name: self.instance.id})
            count = rel_objects.count()

            if count:
                rel_ids = list(rel_objects.values_list('id', flat=True))
                actions = self._build_external_actions(_name, rel_ids, server, count)

                data.append(
                    {
                        'api': {
                            'model': self.model_to_route(
                                obj.remote_field.model._meta.app_label, obj.remote_field.model._meta.model_name
                            ),
                            'query': {f'{obj.remote_field.name}__id': self.instance.pk},
                        },
                        'text': gettext(obj.remote_field.field.verbose_name),
                        'count': count,
                        'actions': actions,
                    }
                )

        return data

    def _get_related_queryset(self, related_model, related_object, user):
        """Get queryset for related objects based on model type."""
        filter_kwargs = {related_object.field.name: self.instance.id}

        if not hasattr(related_model.objects, 'scope'):
            return related_model.objects.filter(**filter_kwargs)

        if related_model.__name__.lower() == 'computer':
            return related_model.productive.scope(user).filter(**filter_kwargs)

        return related_model.objects.scope(user).filter(**filter_kwargs)

    def _should_exclude_relation(self, related_model, _field):
        """Check if relation should be excluded."""
        is_cid_computer = (
            related_model.__name__.lower() == 'computer'
            and self.instance._meta.model_name == 'attribute'
            and self.instance.property_att.prefix == 'CID'
        )
        is_excluded_link = f'{related_model._meta.model_name} - {_field}' in self._exclude_links

        return is_cid_computer or is_excluded_link

    def _build_relation_entry(self, related_model, related_object, _field, count, actions):
        """Build a single relation data entry."""
        from ...client.models import Computer

        model_name = related_model.__name__.lower()
        text = f'{gettext(related_model._meta.verbose_name_plural)} [{gettext(related_object.field.verbose_name)}]'
        api_model = self.model_to_route(related_model._meta.app_label, related_model._meta.model_name)

        if model_name == 'computer':
            query = {_field: self.instance.id, 'status__in': Computer.PRODUCTIVE_STATUS_CSV}
        else:
            if model_name == 'faultdefinition' and _field == 'users__user_ptr':
                _field = 'users__id'
            query = {_field: self.instance.id}

        return {
            'api': {'model': api_model, 'query': query},
            'text': text,
            'count': count,
            'actions': actions,
        }

    def _get_reverse_relations(self, user, server, related_objects):
        """Get reverse relations (one-to-many, one-to-one, m2m auto-created)."""
        data = []

        for related_object, _ in related_objects:
            related_model, _field = self.transmodel(related_object)

            if not related_model:
                continue

            if related_model._meta.app_label == 'authtoken':
                continue

            if self._should_exclude_relation(related_model, _field):
                continue

            rel_objects = self._get_related_queryset(related_model, related_object, user)
            rel_ids = list(rel_objects.values_list('id', flat=True))
            count = len(rel_ids)

            if not count:
                continue

            actions = self._build_external_actions(related_model.__name__.lower(), rel_ids, server, count)
            entry = self._build_relation_entry(related_model, related_object, _field, count, actions)
            data.append(entry)

        return data

    def _get_related_fields(self):
        """Get related object and m2m fields for this model."""
        related_objects = [
            (f, f.model if f.model != self.instance.__class__ else None)
            for f in self.instance._meta.get_fields()
            if (f.one_to_many or f.one_to_one) and f.auto_created and not f.concrete
        ] + [
            (f, f.model if f.model != self.instance.__class__ else None)
            for f in self.instance._meta.get_fields(include_hidden=True)
            if f.many_to_many and f.auto_created
        ]

        objs = [
            (f, f.model if f.model != self.instance.__class__ else None)
            for f in self.instance._meta.get_fields()
            if (f.many_to_many or f.many_to_one) and not f.auto_created
        ]

        return related_objects, objs

    def get_relations(self, request):
        user = request.user.userprofile
        server = request.META.get('HTTP_HOST')

        related_objects, objs = self._get_related_fields()

        data = self._get_self_actions(server)

        data.extend(self._get_m2m_relations(user, server, objs))

        data.extend(self._get_reverse_relations(user, server, related_objects))

        data.extend(self._get_special_relations(user, server, request))

        data.extend(self._get_custom_links())

        return data

    def _get_special_relations(self, user, server, request):
        """Get special relations for models with custom related_objects method."""
        from ...client.models import Computer

        data = []
        actions = []

        if self.instance._meta.model_name.lower() in [
            'device',
            'deployment',
            'scope',
            'domain',
            'attributeset',
            'faultdefinition',
            'platform',
        ]:
            rel_objects = self.instance.related_objects('computer', user)
            if rel_objects is not None:
                # Fetch IDs once and derive count from that
                rel_ids = list(rel_objects.values_list('id', flat=True))
                count = len(rel_ids)
                if count:
                    actions = self._build_external_actions('computer', rel_ids, server, count)

                    if self.instance._meta.model_name.lower() == 'platform':
                        data.append(
                            {
                                'api': {
                                    'model': 'computers',
                                    'query': {
                                        'platform__id': self.instance.id,
                                        'status__in': ','.join(Computer.PRODUCTIVE_STATUS),
                                    },
                                },
                                'text': gettext(self.related_title(rel_objects)),
                                'count': count,
                                'actions': actions,
                            }
                        )
                    elif self.instance._meta.model_name.lower() == 'device':
                        from ..models.attribute import Attribute

                        data.append(
                            {
                                'api': {
                                    'model': 'computers',
                                    'query': {
                                        'sync_attributes__id__in': ','.join(
                                            map(
                                                str,
                                                list(
                                                    Attribute.objects.scope(request.user.userprofile)
                                                    .filter(logical__device__id=self.instance.id)
                                                    .values_list('id', flat=True)
                                                ),
                                            )
                                        ),
                                        'status__in': Computer.PRODUCTIVE_STATUS_CSV,
                                    },
                                },
                                'text': gettext(self.related_title(rel_objects)),
                                'count': count,
                                'actions': actions,
                            }
                        )
                    else:
                        data.append(
                            {
                                'api': {
                                    'model': 'computers',
                                    'query': {'id__in': ','.join(map(str, rel_ids))},
                                },
                                'text': gettext(self.related_title(rel_objects)),
                                'count': count,
                                'actions': actions,
                            }
                        )

        # Special case: installed packages for computer
        if self.instance._meta.model_name.lower() == 'computer':
            installed_packages_count = self.instance.packagehistory_set.filter(
                package__project=self.instance.project, uninstall_date__isnull=True
            ).count()
            if installed_packages_count > 0:
                data.append(
                    {
                        'api': {
                            'model': self.model_to_route('client', 'packagehistory'),
                            'query': {
                                'computer__id': self.instance.id,
                                'package__project__id': self.instance.project.id,
                                'uninstall_date': True,  # isnull = True
                            },
                        },
                        'text': f'{gettext("Installed Packages")} [{gettext("computer")}]',
                        'count': installed_packages_count,
                        'actions': actions,
                    }
                )

        # Special case: computers with package installed
        if self.instance._meta.model_name.lower() == 'package':
            computers_count = self.instance.packagehistory_set.filter(package=self.instance, uninstall_date__isnull=True).count()
            if computers_count > 0:
                data.append(
                    {
                        'api': {
                            'model': self.model_to_route('client', 'computer'),
                            'query': {'installed_package': self.instance.id},
                        },
                        'text': f'{gettext("Installed package")} [{gettext("computer")}]',
                        'count': computers_count,
                        'actions': actions,
                    }
                )

        return data

    def _get_custom_links(self):
        """Get custom included links."""
        data = []

        for _include in self._include_links:
            try:
                _model_name, _field_name = _include.split(' - ')
                data.append(
                    {
                        'api': {
                            'model': self.model_to_route(self.instance._meta.app_label, _model_name),
                            'query': {f'{_field_name}__id': self.instance.id},
                        },
                        'text': f'{gettext(_model_name)} [{gettext(_field_name)}]',
                    }
                )
            except ValueError:
                pass

        return data

    def _get_domain_and_att(self):
        if self.instance._meta.model_name == 'domain':
            from ..models import ServerAttribute

            domain = self.instance
            try:
                att = ServerAttribute.objects.get(value=str(self.instance.name), property_att__prefix='DMN')
            except ObjectDoesNotExist:
                att = None
        else:
            from ..models import Domain

            att = self.instance
            try:
                domain = Domain.objects.get(name=self.instance.value)
            except ObjectDoesNotExist:
                domain = None

        return domain, att

    def _get_attribute_set_and_att(self):
        if self.instance._meta.model_name == 'attributeset':
            from ..models import Attribute

            attribute_set = self.instance
            try:
                att = Attribute.objects.get(value=str(self.instance.name), property_att__prefix='SET')
            except ObjectDoesNotExist:
                att = None
        else:
            from ..models import AttributeSet

            att = self.instance
            try:
                attribute_set = AttributeSet.objects.get(name=self.instance.value)
            except ObjectDoesNotExist:
                attribute_set = None

        return attribute_set, att

    def _get_computer_and_cid(self):
        if self.instance._meta.model_name == 'computer':
            from ..models import Attribute

            computer = self.instance
            try:
                cid = Attribute.objects.get(value=str(self.instance.id), property_att__prefix='CID')
            except ObjectDoesNotExist:
                cid = None
        else:
            from ...client.models import Computer

            cid = self.instance
            computer = Computer.objects.get(pk=int(self.instance.value))

        return computer, cid

    def relations(self, request):
        data = []

        if self.instance._meta.model_name == 'node':
            from ...client.models import Computer

            data.append(
                {
                    'api': {
                        'model': 'computers',
                        'query': {'product': self.instance.computer.product},
                    },
                    'text': f'{gettext("computer")} [{gettext("product")}]',
                    'count': Computer.productive.scope(request.user.userprofile)
                    .filter(product=self.instance.computer.product)
                    .count(),
                    'actions': [],
                }
            )

            return data

        # DOMAIN === ATTRIBUTE
        if self.instance._meta.model_name == 'domain' or (
            self.instance._meta.model_name == 'serverattribute' and self.instance.property_att.prefix == 'DMN'
        ):
            domain, att = self._get_domain_and_att()
            att_data = att.get_relations(request) if att else []
            set_data = domain.get_relations(request) if domain else []
            data = set_data + att_data

            return data

        # ATTRIBUTE SET === ATTRIBUTE
        if self.instance._meta.model_name == 'attributeset' or (
            (self.instance._meta.model_name == 'attribute' and self.instance.pk > 1) and self.instance.property_att.prefix == 'SET'
        ):
            attribute_set, att = self._get_attribute_set_and_att()
            set_data = attribute_set.get_relations(request) if attribute_set else []
            att_data = att.get_relations(request) if att else []
            data = set_data + att_data

            return data

        # COMPUTER === CID ATTRIBUTE
        if self.instance._meta.model_name == 'computer' or (
            (self.instance._meta.model_name in ['attribute', 'clientattribute']) and self.instance.property_att.prefix == 'CID'
        ):
            computer, cid = self._get_computer_and_cid()
            computer_data = computer.get_relations(request) if computer else []
            cid_data = cid.get_relations(request) if cid else []
            data = computer_data + cid_data

            return data

        return self.get_relations(request)

    def _get_related_object(self):
        from ...client.models import Computer
        from ..models import AttributeSet, Domain

        prefix_mapping = {
            'CID': (Computer.objects, 'id', self.instance.value),
            'SET': (AttributeSet.objects, 'name', self.instance.value),
            'DMN': (Domain.objects, 'name', self.instance.value),
        }

        mapping = prefix_mapping.get(self.instance.property_att.prefix)
        if mapping:
            manager, field, value = mapping
            try:
                return manager.get(**{field: value})
            except ObjectDoesNotExist:
                return None

        return None

    def badge(self):
        if self.instance._meta.model_name in ['clientattribute', 'attribute']:
            related_object = self._get_related_object()
            if related_object:
                self.instance = related_object

        badge_data = {
            'pk': self.instance.id,
            'text': escape_format_string(self.instance.__str__()),
        }

        if self.instance._meta.model_name == 'computer':
            badge_data.update(
                {
                    'status': self.instance.status,
                    'summary': f'{self.instance.status}, {self.instance.project}, {self.instance.ip_address}, {self.instance.sync_user}',
                }
            )
        elif self.instance._meta.model_name == 'domain':
            badge_data.update({'status': 'domain', 'summary': gettext(self.instance._meta.verbose_name)})
        elif self.instance._meta.model_name == 'serverattribute' or (
            self.instance._meta.model_name == 'attribute' and self.instance.property_att.sort == 'server'
        ):
            badge_data.update({'status': 'tag', 'summary': gettext(self.instance._meta.verbose_name)})
        elif self.instance._meta.model_name == 'attributeset' or (
            self.instance._meta.model_name in ['clientattribute', 'attribute'] and self.instance.id == 1
        ):
            badge_data.update({'status': 'set', 'summary': f'({gettext(self.instance._meta.verbose_name)}) {self.instance.description}'})
        elif self.instance._meta.model_name == 'clientattribute' or (
            self.instance._meta.model_name == 'attribute' and self.instance.property_att.sort == 'client'
        ):
            badge_data.update({'status': 'attribute', 'summary': self.instance.description})
        elif self.instance._meta.model_name == 'policy':
            badge_data.update({'status': 'policy', 'summary': gettext(self.instance._meta.verbose_name)})

        return badge_data

    def transmodel(self, obj):
        from ...client.models import Computer
        from ..models import ClientAttribute, ServerAttribute

        related_model_lower = obj.related_model._meta.label_lower

        excluded_models = ['admin.logentry', 'core.scheduledelay', 'hardware.node']

        if related_model_lower in excluded_models:
            return '', ''

        if (
            related_model_lower == 'client.computer'
            and self.instance.__class__.__name__ in ['ClientAttribute', 'Attribute']
            and self.instance.property_att.prefix == 'CID'
        ):
            return Computer, 'sync_attributes__id'

        if related_model_lower == 'core.attribute':
            if self.instance.sort == 'server':
                return ServerAttribute, 'property__id'

            return ClientAttribute, 'property__id'

        if related_model_lower == 'client.computer' and self.instance.__class__.__name__ in [
            'ClientAttribute',
            'Attribute',
            'ServerAttribute',
        ]:
            if obj.field.related_model._meta.model_name == 'serverattribute':
                return Computer, 'tags__id'

            if obj.field.related_model._meta.model_name == 'attribute':
                return Computer, 'sync_attributes__id'

        if obj.field.__class__.__name__ in ['ManyRelatedManager', 'OneToOneField', 'ForeignKey']:
            return obj.related_model, f'{obj.field.name}__id'

        return obj.related_model, f'{obj.field.name}__{obj.field.m2m_reverse_target_field_name()}'
