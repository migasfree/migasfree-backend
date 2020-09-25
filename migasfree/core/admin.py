# -*- coding: utf-8 -*-

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

import os

from past.builtins import cmp

from django.db.models import Q, Prefetch
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportActionModelAdmin

from ..client.models import Computer

from .resources import AttributeResource, ProjectResource
from . import tasks

from .models import *
from .forms import (
    PackageForm, DeploymentForm, ClientPropertyForm,
    UserProfileForm, ScopeForm, DomainForm, StoreForm,
    ExternalSourceForm, InternalSourceForm,
)

admin.site.register(Platform)
admin.site.register(Attribute)


@admin.register(Project)
class ProjectAdmin(ImportExportActionModelAdmin):
    resource_class = ProjectResource
    list_display = (
        'name',
        'platform',
        'pms',
        'auto_register_computers'
    )
    list_filter = ('platform', 'pms',)
    list_select_related = ('platform',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    form = StoreForm
    list_display = ('name', 'project')
    list_filter = ('project__name',)
    search_fields = ('name',)
    read_only_fields = ('slug',)
    fields = ('name', 'project')

    def get_queryset(self, request):
        return super(StoreAdmin, self).get_queryset(
            request
        ).select_related('project')


class ClientPropertyFilter(SimpleListFilter):
    title = 'Client Property'
    parameter_name = 'Client Property'

    def lookups(self, request, model_admin):
        return [(c.id, c.name) for c in Property.objects.filter(sort='client')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(id__exact=self.value())
        else:
            return queryset.filter(sort='client')


@admin.register(ClientProperty)
class ClientPropertyAdmin(admin.ModelAdmin):
    form = ClientPropertyForm
    list_display = ('name', 'prefix', 'enabled', 'kind')
    list_filter = ('enabled', 'kind', ClientPropertyFilter)
    ordering = ('name',)
    search_fields = ('name', 'prefix',)
    fields = (
        'prefix', 'name', 'enabled',
        'language', 'code', 'kind',
    )


class ServerPropertyFilter(SimpleListFilter):
    title = 'Server Property'
    parameter_name = 'Server Property'

    def lookups(self, request, model_admin):
        return [(c.id, c.name) for c in Property.objects.filter(sort='server')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(id__exact=self.value())
        else:
            return queryset.filter(sort='server')


@admin.register(ServerProperty)
class ServerPropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'prefix', 'enabled', 'kind')
    fields = ('prefix', 'name', 'kind', 'enabled')
    list_filter = (ServerPropertyFilter,)


class ClientAttributeFilter(SimpleListFilter):
    title = 'Client Attribute'
    parameter_name = 'Client Attribute'

    def lookups(self, request, model_admin):
        return [
            (c.id, c.name) for c in Property.objects.filter(
                Q(sort='client') | Q(sort='basic')
            )
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(property_att__id__exact=self.value())
        else:
            return queryset


@admin.register(ClientAttribute)
class ClientAttributeAdmin(ImportExportActionModelAdmin):
    list_display = ('id', 'property_att', 'value', 'description')
    list_select_related = ('property_att',)
    list_filter = (ClientAttributeFilter,)
    ordering = ('property_att', 'value',)
    search_fields = ('value', 'description')
    readonly_fields = ('property_att', 'value',)
    resource_class = AttributeResource

    def get_queryset(self, request):
        sql = Attribute.TOTAL_COMPUTER_QUERY
        user = request.user.userprofile
        if not user.is_view_all():
            computers = user.get_computers()
            if computers:
                sql += " AND client_computer_sync_attributes.computer_id IN " \
                    + "(" + ",".join(str(x) for x in computers) + ")"
        return ClientAttribute.objects.scope(user).extra(
            select={'total_computers': sql}
        )


class ServerAttributeFilter(SimpleListFilter):
    title = 'Server Attribute'
    parameter_name = 'Server Attribute'

    def lookups(self, request, model_admin):
        return [(c.id, c.name) for c in Property.objects.filter(sort='server')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(property_att__id__exact=self.value())
        else:
            return queryset


@admin.register(ServerAttribute)
class ServerAttributeAdmin(ImportExportActionModelAdmin):
    list_display = ('value', 'description', 'property_att')
    fields = ('property_att', 'value', 'description', 'inflicted_computers')
    list_filter = (ServerAttributeFilter,)
    ordering = ('property_att', 'value',)
    search_fields = ('value', 'description')
    readonly_fields = ('inflicted_computers',)
    resource_class = AttributeResource

    def get_queryset(self, request):
        sql = Attribute.TOTAL_COMPUTER_QUERY
        user = request.user.userprofile
        if not user.is_view_all():
            computers = user.get_computers()
            if computers:
                sql += " AND client_computer_sync_attributes.computer_id IN " \
                    + "(" + ",".join(str(x) for x in computers) + ")"
        return ServerAttribute.objects.scope(user).extra(
            select={'total_computers': sql}
        )

    def inflicted_computers(self, obj):
        ret = [
            c.__str__() for c in Computer.productive.filter(
                sync_attributes__in=[obj.pk]
            ).exclude(tags__in=[obj.pk])
        ]

        return format_html('<br />'.join(ret))

    inflicted_computers.short_description = _('Inflicted Computers')


@admin.register(AttributeSet)
class AttributeSetAdmin(admin.ModelAdmin):
    list_display = ('name', 'enabled')
    list_display_links = ('name',)
    list_filter = ('enabled',)
    search_fields = ('name', 'included_attributes__value', 'excluded_attributes__value')

    def get_queryset(self, request):
        qs = Attribute.objects.scope(request.user.userprofile)
        return super(AttributeSetAdmin, self).get_queryset(
            request
        ).prefetch_related(
            Prefetch('included_attributes', queryset=qs),
            'included_attributes__property_att',
            Prefetch('excluded_attributes', queryset=qs),
            'excluded_attributes__property_att'
        )


class ScheduleDelayLine(admin.TabularInline):
    model = ScheduleDelay
    fields = ('delay', 'attributes', 'computers', 'duration')
    readonly_fields = ('computers',)
    extra = 0
    ordering = ('delay',)

    def computers(self, obj):
        related_objects = obj.related_objects('computer', self.request.user.userprofile)
        if related_objects:
            return related_objects.count()

        return 0

    computers.short_description = _('Computers')

    def get_queryset(self, request):
        self.request = request
        qs = Attribute.objects.scope(request.user.userprofile)

        return super(ScheduleDelayLine, self).get_queryset(
            request
        ).prefetch_related(
            Prefetch('attributes', queryset=qs),
            'attributes__property_att',
        )


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'number_delays')
    search_fields = ('name', 'description')
    ordering = ('name',)
    inlines = [ScheduleDelayLine, ]
    extra = 0

    fieldsets = (
        ('', {
            'fields': (
                'name',
                'project',
            )
        }),
    )

    def get_queryset(self, request):
        self.request = request

        return super(ScheduleAdmin, self).get_queryset(
            request
        )


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    form = PackageForm

    list_display = ('name', 'version', 'architecture', 'project', 'store')
    list_filter = ('project__platform', 'project__name', 'store', 'deployment')
    list_select_related = ('project', 'store',)
    search_fields = ('name', 'store__name',)
    ordering = ('name',)

    def get_queryset(self, request):
        return super(PackageAdmin, self).get_queryset(
            request
        ).prefetch_related(
            Prefetch('deployment_set', queryset=Deployment.objects.scope(request.user.userprofile))
        )

    def save_model(self, request, obj, form, change):
        package_file = request.FILES['package_file']
        if obj.id:
            if obj.store and package_file:
                Package.handle_uploaded_file(
                    package_file,
                    os.path.join(Store.path(obj.project.slug, obj.store.slug), obj.fullname)
                )
            super(PackageAdmin, self).save_model(request, obj, form, change)
        else:
            Package.objects.create(
                fullname=obj.fullname, project=obj.project,
                name=obj.name, version=obj.version,
                architecture=obj.architecture,
                store=obj.store,
                file_=package_file
            )


@admin.register(PackageSet)
class PackageSetAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    ordering = ('name',)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'packages':
            kwargs["queryset"] = Package.objects.filter(
                store__isnull=False
            )

            return db_field.formfield(**kwargs)

        return super(PackageSetAdmin, self).formfield_for_manytomany(
            db_field, request, **kwargs
        )


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
        (_('General'), {
            'fields': ('name', 'slug', 'enabled', 'project', 'comment')
        }),
        (_('What (Packages)'), {
            'classes': ('collapse',),
            'fields': (
                'available_packages',
                'available_package_sets',
                'packages_to_install',
                'packages_to_remove',
            )
        }),
        (_('To whom (Attributes)'), {
            'classes': ('collapse',),
            'fields': (
                'domain',
                'included_attributes',
                'excluded_attributes'
            )
        }),
        (_('When (Schedule)'), {
            'fields': (
                'start_date',
                'schedule'
            )
        }),
        (_('Packages by default'), {
            'classes': ('collapse',),
            'fields': (
                'default_preincluded_packages',
                'default_included_packages',
                'default_excluded_packages',
            )
        }),
    )

    def computers(self, obj):
        related_objects = obj.related_objects('computer', self.user.userprofile)
        if related_objects:
            return related_objects.count()

        return 0

    computers.short_description = _('Computers')

    def save_model(self, request, obj, form, change):
        is_new = (obj.pk is None)
        has_slug_changed = form.initial.get('slug') != obj.slug
        packages_after = form.cleaned_data['available_packages']

        user = request.user.userprofile
        if user:
            obj.domain = user.domain_preference

        if user.domain_preference and user.domain_preference == obj.domain:
            if not obj.name.startswith(user.domain_preference.name.lower()):
                obj.name = '{}_{}'.format(user.domain_preference.name.lower(), obj.name)

        super(DeploymentAdmin, self).save_model(request, obj, form, change)

        # create repository metadata when packages has been changed
        # or repository not have packages at first time
        # or name (slug) is changed (to avoid client errors)
        if ((is_new and len(packages_after) == 0)
                or cmp(
                    sorted(
                        obj.available_packages.values_list('id', flat=True)
                    ),  # packages before
                    sorted(packages_after)
                ) != 0) or has_slug_changed:
            tasks.create_repository_metadata.delay(obj.id)

            # delete old repository when name (slug) has changed
            if has_slug_changed and not is_new:
                tasks.remove_repository_metadata.delay(obj.id, form.initial.get('slug'))

    def get_queryset(self, request):
        self.user = request.user
        qs = Attribute.objects.scope(request.user.userprofile)

        return super(DeploymentAdmin, self).get_queryset(
            request
        ).prefetch_related(
            Prefetch('included_attributes', queryset=qs),
            'included_attributes__property_att',
            Prefetch('excluded_attributes', queryset=qs),
            'excluded_attributes__property_att',
        ).extra(
            select={
                'schedule_begin': '(SELECT delay FROM core_scheduledelay '
                                  'WHERE core_deployment.schedule_id = core_scheduledelay.schedule_id '
                                  'ORDER BY core_scheduledelay.delay LIMIT 1)',
                'schedule_end': '(SELECT delay+duration FROM core_scheduledelay '
                                'WHERE core_deployment.schedule_id = core_scheduledelay.schedule_id '
                                'ORDER BY core_scheduledelay.delay DESC LIMIT 1)'
             }
        ).select_related('project', 'schedule')


@admin.register(ExternalSource)
class ExternalSourceAdmin(DeploymentAdmin):
    form = ExternalSourceForm
    fieldsets = (
        (_('General'), {
            'fields': (
                'name',
                'slug',
                'project',
                'enabled',
                'comment',
            )
        }),
        (_('Source'), {
            'fields': ('base_url', 'suite', 'components', 'options', 'frozen', 'expire',)
        }),
        (_('What (Packages)'), {
            'classes': ('collapse',),
            'fields': (
                'packages_to_install',
                'packages_to_remove',
            )
        }),
        (_('Packages by default'), {
            'classes': ('collapse',),
            'fields': (
                'default_preincluded_packages',
                'default_included_packages',
                'default_excluded_packages',
            )
        }),
        (_('To whom (Attributes)'), {
            'fields': (
                'domain',
                'included_attributes',
                'excluded_attributes'
            )
        }),
        (_('When (Schedule)'), {
            'fields': (
                'start_date',
                'schedule',
            )
        }),
    )


@admin.register(InternalSource)
class InternalSourceAdmin(DeploymentAdmin):
    form = InternalSourceForm
    fieldsets = (
        (_('General'), {
            'fields': ('name', 'slug', 'project', 'enabled', 'comment',)
        }),
        (_('What (Packages)'), {
            'classes': ('collapse',),
            'fields': (
                'available_packages',
                'available_package_sets',
                'packages_to_install',
                'packages_to_remove',
            )
        }),
        (_('Packages by default'), {
            'classes': ('collapse',),
            'fields': (
                'default_preincluded_packages',
                'default_included_packages',
                'default_excluded_packages',
            )
        }),
        (_('To whom (Attributes)'), {
            'fields': ('domain', 'included_attributes', 'excluded_attributes')
        }),
        (_('When (Schedule)'), {
            'fields': ('start_date', 'schedule')
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    form = UserProfileForm
    list_display = ('username', 'first_name', 'last_name', 'domain_preference')
    ordering = ('username',)
    search_fields = ('username', 'first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_login')
    actions = ['activate_users']

    fieldsets = (
         (_('General'), {
             'fields': (
                 'username',
                 'first_name',
                 'last_name',
                 'email',
                 'date_joined',
                 'last_login',
             ),
         }),
         (_('Authorizations'), {
             'fields': (
                 'is_active',
                 'is_superuser',
                 'is_staff',
                 'groups',
                 'user_permissions',
                 'domains',
             ),
         }),
         (_('Preferences'), {
            'fields': (
                'domain_preference',
                'scope_preference',
            ),
         }),
    )

    def activate_users(self, request, queryset):
        cnt = queryset.filter(is_active=False).update(is_active=True)
        self.message_user(request, 'Activated {} users.'.format(cnt))

    activate_users.short_description = _('Activate Users')

    def get_actions(self, request):
        actions = super(UserProfileAdmin, self).get_actions(request)
        if not request.user.has_perm('auth.change_user'):
            del actions['activate_users']

        return actions

    def get_form(self, request, obj=None, **kwargs):
        form = super(UserProfileAdmin, self).get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        disabled_fields = set()

        if not is_superuser:
            disabled_fields |= {
                'username',
                'is_superuser',
                'user_permissions',
            }

        # Prevent non-superusers from editing their own permissions
        if (
            not is_superuser
            and obj is not None
            and obj == request.user
        ):
            disabled_fields |= {
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            }

        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True

        return form


@admin.register(Scope)
class ScopeAdmin(admin.ModelAdmin):
    form = ScopeForm
    list_display = ('name', 'domain')
    ordering = ('name',)
    search_fields = ('name',)
    fieldsets = (
        (_('General'), {
            'fields': (
                'name',
                'domain'
            ),
        }),
        (_('Attributes'), {
            'fields': (
                'included_attributes',
                'excluded_attributes',
            ),
        }),
        ('', {
            'fields': ('user',),
            'classes': ['hidden'],
        })
    )

    def get_queryset(self, request):
        qs = Attribute.objects.scope(request.user.userprofile)

        return super(ScopeAdmin, self).get_queryset(
            request
        ).prefetch_related(
            Prefetch('included_attributes', queryset=qs),
            'included_attributes__property_att',
            Prefetch('excluded_attributes', queryset=qs),
            'excluded_attributes__property_att'
        )


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    form = DomainForm
    list_display = ('name',)
    ordering = ('name',)
    search_fields = ('name',)
    fieldsets = (
        (_('General'), {
            'fields': (
                'name', 'comment',
            ),
        }),
        (_('Attributes'), {
            'fields': (
                'included_attributes',
                'excluded_attributes',
             ),
        }),
        (_('Available tags'), {
            'fields': (
                'tags',
            ),
        }),
    )

    def get_queryset(self, request):
        user_profile = UserProfile.objects.get(id=request.user.id)
        user_profile.update_scope(0)

        return super(DomainAdmin, self).get_queryset(request)
