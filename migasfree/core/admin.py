# -*- coding: utf-8 -*-

# Copyright (c) 2015-2016 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2016 Alberto Gacías <alberto@migasfree.org>
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

from django.db.models import Q
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext_lazy as _

from import_export import resources, fields, widgets
from import_export.admin import ImportExportActionModelAdmin

from . import tasks

from .models import *
from .forms import PackageForm, DeploymentForm, ClientPropertyForm

admin.site.register(Platform)


class ProjectResource(resources.ModelResource):
    autoregister = fields.Field(
        attribute='autoregister',
        widget=widgets.BooleanWidget()
    )

    class Meta:
        model = Project
        fields = ('name', 'pms', 'autoregister', 'platform__name')


@admin.register(Project)
class ProjectAdmin(ImportExportActionModelAdmin):
    resource_class = ProjectResource
    list_display = (
        'name',
        'platform',
        'pms',
        'autoregister'
    )
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'project')
    list_filter = ('project__name',)
    search_fields = ('name',)
    read_only_fields = ('slug',)
    fields = ('name', 'project')


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
    list_filter = ('enabled', ClientPropertyFilter)
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
    fields = ('property_att', 'value', 'description')
    list_filter = (ServerAttributeFilter,)
    ordering = ('property_att', 'value',)
    search_fields = ('value', 'description')


@admin.register(SetOfAttributes)
class SetOfAttributesAdmin(admin.ModelAdmin):
    model = SetOfAttributes


class ScheduleDelayLine(admin.TabularInline):
    model = ScheduleDelay
    extra = 0
    ordering = ('delay',)


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'number_delays')
    ordering = ('name',)
    inlines = [ScheduleDelayLine, ]
    extra = 0


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    form = PackageForm

    list_display = ('name', 'project', 'store')
    # list_display_links = None
    list_filter = ('project__name', 'store',)
    list_select_related = ('project',)
    list_per_page = 25
    search_fields = ('name', 'store__name',)
    ordering = ('name',)

    def save_model(self, request, obj, form, change):
        file_list = request.FILES.getlist('package_file')
        Package.objects.create(obj.name, obj.project, obj.store, file_list)


@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    form = DeploymentForm
    list_display = ('name', 'project', 'enabled', 'start_date',)
    list_select_related = ('schedule',)
    list_filter = ('enabled', 'project__name',)
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

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == "included_attributes":
            kwargs["queryset"] = Attribute.objects.filter(
                property_att__enabled=True
            )

            return db_field.formfield(**kwargs)

        return super(DeploymentAdmin, self).formfield_for_manytomany(
            db_field, request, **kwargs
        )

    def save_model(self, request, obj, form, change):
        is_new = (obj.pk is None)
        packages_after = form.cleaned_data['available_packages']
        super(DeploymentAdmin, self).save_model(request, obj, form, change)

        old_slug = form.initial.get('slug')
        new_slug = obj.slug

        # create repository metadata when packages has been changed
        # or repository not have packages at first time
        # or name (slug) is changed (to avoid client errors)
        if ((is_new and len(packages_after) == 0)
                or cmp(
                    sorted(
                        obj.available_packages.values_list('id', flat=True)
                    ),  # packages before
                    sorted(packages_after)
                ) != 0) or (new_slug != old_slug):
            tasks.create_repository_metadata.delay(obj.id)

            # delete old repository when name (slug) has changed
            if new_slug != old_slug and not is_new:
                tasks.remove_repository_metadata.delay(obj.id, old_slug)
