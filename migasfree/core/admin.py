# -*- coding: utf-8 -*-

# Copyright (c) 2015-2018 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2018 Alberto Gacías <alberto@migasfree.org>
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

from django.db.models import Q, Prefetch
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from import_export import resources, fields, widgets
from import_export.admin import ImportExportActionModelAdmin

from migasfree.client.models import Computer

from . import tasks

from .models import *
from .forms import (
    PackageForm, DeploymentForm, ClientPropertyForm,
    UserProfileForm, ScopeForm, DomainForm, StoreForm,
)

admin.site.register(Platform)


class ProjectResource(resources.ModelResource):
    auto_register_computers = fields.Field(
        attribute='auto_register_computers',
        widget=widgets.BooleanWidget()
    )

    class Meta:
        model = Project
        fields = ('name', 'pms', 'auto_register_computers', 'platform__name')


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
class ClientAttributeAdmin(admin.ModelAdmin):
    list_display = ('id', 'property_att', 'value', 'description')
    list_select_related = ('property_att',)
    list_filter = (ClientAttributeFilter,)
    ordering = ('property_att', 'value',)
    search_fields = ('value', 'description')
    readonly_fields = ('property_att', 'value',)

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
class ServerAttributeAdmin(admin.ModelAdmin):
    list_display = ('value', 'description', 'property_att')
    fields = ('property_att', 'value', 'description', 'inflicted_computers')
    list_filter = (ServerAttributeFilter,)
    ordering = ('property_att', 'value',)
    search_fields = ('value', 'description')
    readonly_fields = ('inflicted_computers',)

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
        ret = []
        for c in Computer.productive.filter(sync_attributes__in=[obj.pk]).exclude(tags__in=[obj.pk]):
            ret.append(c.__str__())

        return format_html('<br />'.join(ret))

    inflicted_computers.short_description = _('Inflicted Computers')


@admin.register(AttributeSet)
class AttributeSetAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_display_links = ('name',)
    list_filter = ('enabled',)
    search_fields = ('name', 'included_attributes__value', 'excluded_attributes__value')


class ScheduleDelayLine(admin.TabularInline):
    model = ScheduleDelay
    extra = 0
    ordering = ('delay',)

    def get_queryset(self, request):
        sql = ScheduleDelay.TOTAL_COMPUTER_QUERY
        user = request.user.userprofile
        if not user.is_view_all():
            computers = user.get_computers()
            if computers:
                sql += " AND client_computer_sync_attributes.computer_id IN " \
                    + "(" + ",".join(str(x) for x in computers) + ")"
            qs = ScheduleDelay.objects.scope(user).extra(select={'total_computers': sql})
        else:
            qs = ScheduleDelay.objects.all()

        return qs


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


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    form = PackageForm

    list_display = ('name', 'version', 'architecture', 'project', 'store')
    list_filter = ('project__name', 'store',)
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
    list_display = ('project', 'name', 'enabled', 'start_date',)
    list_select_related = ('project',)
    list_filter = ('enabled', 'project__name', 'schedule',)
    ordering = ('name',)
    search_fields = ('name', 'available_packages__name',)
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

    def save_model(self, request, obj, form, change):
        is_new = (obj.pk is None)
        has_slug_changed = form.initial.get('slug') != obj.slug
        packages_after = form.cleaned_data['available_packages']

        user = request.user.userprofile
        if user:
            obj.domain = user.domain_preference
        if user.domain_preference:
            if not obj.name.startswith(user.domain_preference.name.lower()):
                obj.name = u'{}_{}'.format(user.domain_preference.name.lower(), obj.name)

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


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    form = UserProfileForm
    list_display = ('username', 'first_name', 'last_name', 'domain_preference')
    ordering = ('username',)
    search_fields = ('username', 'first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_login')

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
