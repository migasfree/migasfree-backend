# Copyright (c) 2015-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2026 Alberto Gacías <alberto@migasfree.org>
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

"""
Deployment admin classes (Deployment, InternalSource, ExternalSource).
"""

from django.contrib import admin
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _

from ...utils import cmp
from ..forms import DeploymentForm, ExternalSourceForm, InternalSourceForm
from ..models import Attribute, Deployment, ExternalSource, InternalSource
from ..pms import tasks


@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    form = DeploymentForm
    list_display = ('project', 'name', 'enabled', 'domain', 'start_date', 'computers')
    list_select_related = ('project',)
    list_filter = ('enabled', 'project__name', 'domain')
    ordering = ('name',)
    search_fields = ('name', 'available_packages__name')
    read_only_fields = ('slug',)
    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        (_('General'), {'fields': ('name', 'slug', 'enabled', 'project', 'comment')}),
        (
            _('What (Packages)'),
            {
                'classes': ('collapse',),
                'fields': (
                    'available_packages',
                    'available_package_sets',
                    'packages_to_install',
                    'packages_to_remove',
                ),
            },
        ),
        (
            _('To whom (Attributes)'),
            {'classes': ('collapse',), 'fields': ('domain', 'included_attributes', 'excluded_attributes')},
        ),
        (_('When (Schedule)'), {'fields': ('start_date', 'schedule')}),
        (
            _('Packages by default'),
            {
                'classes': ('collapse',),
                'fields': (
                    'default_preincluded_packages',
                    'default_included_packages',
                    'default_excluded_packages',
                ),
            },
        ),
    )

    def computers(self, obj):
        related_objects = obj.related_objects('computer', self.user.userprofile)
        return related_objects.count() if related_objects else 0

    computers.short_description = _('Computers')

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        has_slug_changed = form.initial.get('slug') != obj.slug
        packages_after = form.cleaned_data['available_packages']

        user = request.user.userprofile
        if user and user.domain_preference:
            obj.domain = user.domain_preference
            prefix = user.domain_preference.name.lower()
            if not obj.name.startswith(f'{prefix}_'):
                obj.name = f'{prefix}_{obj.name}'

        super().save_model(request, obj, form, change)

        # Create repository metadata when needed
        packages_changed = (
            cmp(
                sorted(obj.available_packages.values_list('id', flat=True)),
                sorted(packages_after),
            )
            != 0
        )

        should_create_metadata = (is_new and not packages_after) or packages_changed or has_slug_changed

        if should_create_metadata:
            tasks.create_repository_metadata.apply_async(
                queue=f'pms-{obj.pms().name}', kwargs={'deployment_id': obj.id}
            )

            if has_slug_changed and not is_new:
                tasks.remove_repository_metadata.delay(obj.id, form.initial.get('slug'))

    def get_queryset(self, request):
        self.user = request.user
        qs = Attribute.objects.scope(request.user.userprofile)

        return (
            Deployment.objects.scope(request.user.userprofile)
            .prefetch_related(
                Prefetch('included_attributes', queryset=qs),
                'included_attributes__property_att',
                Prefetch('excluded_attributes', queryset=qs),
                'excluded_attributes__property_att',
            )
            .extra(
                select={
                    'schedule_begin': '(SELECT delay FROM core_scheduledelay '
                    'WHERE core_deployment.schedule_id = core_scheduledelay.schedule_id '
                    'ORDER BY core_scheduledelay.delay LIMIT 1)',
                    'schedule_end': '(SELECT delay+duration FROM core_scheduledelay '
                    'WHERE core_deployment.schedule_id = core_scheduledelay.schedule_id '
                    'ORDER BY core_scheduledelay.delay DESC LIMIT 1)',
                }
            )
        )


@admin.register(ExternalSource)
class ExternalSourceAdmin(DeploymentAdmin):
    form = ExternalSourceForm
    fieldsets = (
        (
            _('General'),
            {
                'fields': (
                    'name',
                    'slug',
                    'project',
                    'enabled',
                    'comment',
                )
            },
        ),
        (
            _('Source'),
            {
                'fields': (
                    'base_url',
                    'suite',
                    'components',
                    'options',
                    'frozen',
                    'expire',
                )
            },
        ),
        (
            _('What (Packages)'),
            {
                'classes': ('collapse',),
                'fields': (
                    'packages_to_install',
                    'packages_to_remove',
                ),
            },
        ),
        (
            _('Packages by default'),
            {
                'classes': ('collapse',),
                'fields': (
                    'default_preincluded_packages',
                    'default_included_packages',
                    'default_excluded_packages',
                ),
            },
        ),
        (_('To whom (Attributes)'), {'fields': ('domain', 'included_attributes', 'excluded_attributes')}),
        (
            _('When (Schedule)'),
            {
                'fields': (
                    'start_date',
                    'schedule',
                )
            },
        ),
    )


@admin.register(InternalSource)
class InternalSourceAdmin(DeploymentAdmin):
    form = InternalSourceForm
    fieldsets = (
        (
            _('General'),
            {
                'fields': (
                    'name',
                    'slug',
                    'project',
                    'enabled',
                    'comment',
                )
            },
        ),
        (
            _('What (Packages)'),
            {
                'classes': ('collapse',),
                'fields': (
                    'available_packages',
                    'available_package_sets',
                    'packages_to_install',
                    'packages_to_remove',
                ),
            },
        ),
        (
            _('Packages by default'),
            {
                'classes': ('collapse',),
                'fields': (
                    'default_preincluded_packages',
                    'default_included_packages',
                    'default_excluded_packages',
                ),
            },
        ),
        (_('To whom (Attributes)'), {'fields': ('domain', 'included_attributes', 'excluded_attributes')}),
        (_('When (Schedule)'), {'fields': ('start_date', 'schedule')}),
    )
