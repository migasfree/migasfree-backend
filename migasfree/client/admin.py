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

import os

from django.contrib import admin
from django.shortcuts import redirect
from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from migasfree.core.models import Attribute

from .models import *


def add_computer_search_fields(fields_list):
    for field in settings.MIGASFREE_COMPUTER_SEARCH_FIELDS:
        fields_list.append("computer__%s" % field)

    return tuple(fields_list)


@admin.register(Computer)
class ComputerAdmin(admin.ModelAdmin):
    list_display = (
        '__str__',
        'status',
        'project',
        'ip_address',
        'sync_user',
        'sync_end_date',
    )
    list_per_page = 25
    ordering = (settings.MIGASFREE_COMPUTER_SEARCH_FIELDS[0],)
    list_filter = ('project__name', 'sync_start_date', 'status')
    search_fields = settings.MIGASFREE_COMPUTER_SEARCH_FIELDS + (
        'sync_user', 'sync_user__fullname'
    )

    readonly_fields = (
        'name',
        'uuid',
        'project',
        'created_at',
        'ip_address',
        'sync_start_date',
        'sync_user',
        'sync_attributes',
        'sync_end_date',
        'software_inventory',
        'software_history',
        'hardware',
        'machine',
        'cpu',
        'ram',
        'storage',
        'disks',
        'mac_address',
    )

    fieldsets = (
        (_('General'), {
            'fields': (
                'status',
                'name',
                'project',
                'created_at',
                'ip_address',
            )
        }),
        (_('Hardware'), {
            'fields': (
                'last_hardware_capture',
                'hardware',
                'uuid',
                'machine',
                'cpu',
                'ram',
                'storage',
                'disks',
                'mac_address',
            )
        }),
        (_('Synchronization'), {
            'fields': (
                'sync_start_date',
                'sync_end_date',
                'sync_user',
                'sync_attributes',
            )
        }),
        (_('Tags'), {
            'fields': ('tags',)
        }),
        (_('Software'), {
            'classes': ('grp-collapse grp-closed',),
            'fields': (
                'software_inventory',
                'software_history',
            )
        }),
        #(_('Devices'), {
        #    'fields': ('logical_devices',)
        #}),
    )

    """
    actions = ['delete_selected']

    def delete_selected(self, request, objs):
        if not self.has_delete_permission(request):
            raise PermissionDenied

        return render(
            request,
            'computer_confirm_delete_selected.html',
            {
                'object_list': ', '.join(
                    objs.values_list(
                        settings.MIGASFREE_COMPUTER_SEARCH_FIELDS[0], flat=True
                    )
                )
            }
        )

    delete_selected.short_description = _("Delete selected %(verbose_name_plural)s")
    """

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        '''
        if db_field.name == "logical_devices":
            kwargs['widget'] = FilteredSelectMultiple(
                db_field.verbose_name,
                (db_field.name in self.filter_vertical)
            )
            return db_field.formfield(**kwargs)
        '''

        if db_field.name == "sync_attributes":
            kwargs["queryset"] = Attribute.objects.filter(
                property_att__enabled=True
            )
            return db_field.formfield(**kwargs)

        return super(ComputerAdmin, self).formfield_for_manytomany(
            db_field, request, **kwargs
        )

    def has_add_permission(self, request):
        return False


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('fullname', 'project')
    ordering = ('name', 'version', 'project')
    list_filter = ('project',)
    search_fields = ('name', 'version', 'fullname')
    readonly_fields = (
        'fullname', 'name',
        'version', 'architecture', 'project'
    )

    def has_add_permission(self, request):
        return False


@admin.register(Error)
class ErrorAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'computer',
        'project',
        'checked',
        'created_at',
        'truncated_desc',
    )
    list_filter = ('checked', 'created_at', 'project__name')
    #list_editable = ('checked',)  # TODO
    ordering = ('-created_at', 'computer',)
    search_fields = add_computer_search_fields(['created_at', 'description'])
    readonly_fields = ('computer', 'project', 'created_at', 'description')
    exclude = ('computer',)

    actions = ['checked_ok']

    def checked_ok(self, request, queryset):
        for error in queryset:
            error.checked_ok()

        return redirect(request.get_full_path())

    checked_ok.short_description = _("Checking is O.K.")

    def has_add_permission(self, request):
        return False


@admin.register(FaultDefinition)
class FaultDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'enabled',
        'list_included_attributes', 'list_excluded_attributes',
        'list_users'
    )
    list_filter = ('enabled',)
    ordering = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('included_attributes',)

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'enabled', 'language', 'code')
        }),
        (_('Atributtes'), {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('included_attributes', 'excluded_attributes')
        }),
        (_('Users'), {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('users',)
        }),
    )


class UserFaultFilter(SimpleListFilter):
    title = _('User')
    parameter_name = 'user'

    def lookups(self, request, model_admin):
        return Fault.USER_FILTER_CHOICES

    def queryset(self, request, queryset):
        me = request.user.id
        if self.value() == 'me':
            return queryset.filter(
                Q(fault_definition__users__id=me)
                | Q(fault_definition__users=None)
            )
        elif self.value() == 'only_me':
            return queryset.filter(fault_definition__users__id=me)
        elif self.value() == 'others':
            return queryset.exclude(
                fault_definition__users__id=me
            ).exclude(fault_definition__users=None)
        elif self.value() == 'unassigned':
            return queryset.filter(fault_definition__users=None)


@admin.register(Fault)
class FaultAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'computer',
        'project',
        'checked',
        'created_at',
        'result',
        'fault_definition',
        #'list_users'  # performance improvement
    )
    list_filter = (
        UserFaultFilter,
        'checked', 'created_at', 'project__name', 'fault_definition'
    )
    ordering = ('-created_at', 'computer',)
    search_fields = add_computer_search_fields(
        ['created_at', 'fault_definition__name']
    )
    readonly_fields = (
        'computer', 'fault_definition', 'project', 'created_at', 'result'
    )
    exclude = ('computer',)

    actions = ['checked_ok']

    def checked_ok(self, request, queryset):
        for fault in queryset:
            fault.checked_ok()

        return redirect(request.get_full_path())

    checked_ok.short_description = _("Checking is O.K.")

    def has_add_permission(self, request):
        return False


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'fullname',)
    ordering = ('name',)
    search_fields = ('name', 'fullname')
    readonly_fields = ('name', 'fullname')

    def has_add_permission(self, request):
        return False


@admin.register(Migration)
class MigrationAdmin(admin.ModelAdmin):
    list_display = ('id', 'computer', 'project', 'created_at')
    list_select_related = ('computer', 'project',)
    list_filter = ('created_at', 'project__name', 'project__platform__name',)
    search_fields = add_computer_search_fields(['created_at'])
    readonly_fields = ('computer', 'project', 'created_at')
    exclude = ("computer",)
    actions = None

    def has_add_permission(self, request):
        return False


@admin.register(Synchronization)
class SynchronizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'computer', 'user', 'created_at', 'project')
    list_filter = ('created_at', 'pms_status_ok')
    search_fields = add_computer_search_fields(['created_at', 'user__name'])
    readonly_fields = (
        'computer', 'user', 'project', 'created_at',
        'start_date', 'consumer', 'pms_status_ok'
    )
    exclude = ('computer',)
    actions = None

    def has_add_permission(self, request):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'message', 'checked')
    list_filter = ('checked', 'created_at')
    ordering = ('-created_at',)
    search_fields = ('message',)
    readonly_fields = ('created_at', 'message')

    def has_add_permission(self, request):
        return False


@admin.register(StatusLog)
class StatusLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'created_at')
    list_select_related = ('computer', )
    list_filter = ('created_at', 'status')
    search_fields = add_computer_search_fields(['created_at'])
    readonly_fields = ('status', 'created_at')
    exclude = ('computer',)
    actions = None

    def has_add_permission(self, request):
        return False
