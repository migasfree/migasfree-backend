# -*- coding: utf-8 -*-

# Copyright (c) 2015-2022 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2022 Alberto Gacías <alberto@migasfree.org>
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

from django.db.models import Q, Prefetch
from django.contrib import admin
from django.shortcuts import redirect
from django.contrib.admin import SimpleListFilter
from django.urls import resolve
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from ..core.models import Attribute
from ..device.models import Logical
from ..hardware.models import Node

from .models import (
    Computer, PackageHistory, Error, Fault, FaultDefinition,
    User, Migration, Synchronization, Notification, StatusLog,
)


def add_computer_search_fields(fields_list):
    for field in settings.MIGASFREE_COMPUTER_SEARCH_FIELDS:
        fields_list.append(f'computer__{field}')

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
    list_filter = (
        'project__platform', 'project__name',
        'sync_start_date', 'status', 'machine'
    )
    search_fields = settings.MIGASFREE_COMPUTER_SEARCH_FIELDS + (
        'sync_user', 'sync_user__fullname'
    )

    readonly_fields = (
        'name',
        'fqdn',
        'uuid',
        'project',
        'created_at',
        'ip_address',
        'forwarded_ip_address',
        'sync_start_date',
        'sync_user',
        'sync_attributes',
        'sync_end_date',
        'get_software_inventory',
        'get_software_history',
        'hardware',
        'machine',
        'cpu',
        'ram',
        'storage',
        'disks',
        'mac_address',
        'my_inflicted_logical_devices',
    )

    fieldsets = (
        (_('General'), {
            'fields': (
                'status',
                'name',
                'fqdn',
                'project',
                'created_at',
                'ip_address',
                'forwarded_ip_address',
                'comment',
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
                'get_software_inventory',
                'get_software_history',
            )
        }),
        (_('Devices'), {
            'fields': (
                'my_inflicted_logical_devices',
                # 'assigned_logical_devices_to_cid',
                'default_logical_device',
            )
        }),
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

    def get_software_inventory(self, obj):
        return '\n'.join(obj.get_software_inventory())

    get_software_inventory.short_description = _('Software Inventory')

    def get_software_history(self, obj):
        ret = obj.get_software_history()

        return '\n\n'.join(
            "# %s\n%s" % (
                key,
                '\n'.join(v for v in val)
            ) for (key, val) in sorted(ret.items(), reverse=True)
        )

    get_software_history.short_description = _('Software History')

    def my_inflicted_logical_devices(self, obj):
        return ', '.join([item.__str__() for item in obj.inflicted_logical_devices()])

    my_inflicted_logical_devices.short_description = _('Inflicted Logical Devices')

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == "sync_attributes":
            kwargs["queryset"] = Attribute.objects.filter(
                property_att__enabled=True
            )
            return db_field.formfield(**kwargs)

        return super().formfield_for_manytomany(
            db_field, request, **kwargs
        )

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == "default_logical_device":
            computer_id = resolve(request.path).kwargs.get('object_id', 0)
            if computer_id:
                computer = Computer.objects.get(pk=computer_id)
                kwargs['queryset'] = Logical.objects.filter(
                    pk__in=[x.id for x in computer.logical_devices()]
                )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return Computer.objects.scope(request.user.userprofile).prefetch_related(
            Prefetch('node_set', queryset=Node.objects.filter(parent=None)),
        )


@admin.register(PackageHistory)
class PackageHistoryAdmin(admin.ModelAdmin):
    list_display = ('computer', 'package', 'install_date', 'uninstall_date')
    ordering = ('computer', 'package__fullname')
    list_filter = ('computer', 'package')
    search_fields = ('computer__name', 'package__fullname')
    readonly_fields = (
        'computer', 'package',
        'install_date', 'uninstall_date'
    )

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return PackageHistory.objects.scope(request.user.userprofile)


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
    ordering = ('-created_at', 'computer',)
    search_fields = add_computer_search_fields(['created_at', 'description'])
    readonly_fields = ('computer', 'project', 'created_at', 'description')
    exclude = ('computer',)

    actions = ['checked_ok']

    def checked_ok(self, request, queryset):
        for item in queryset:
            item.checked_ok()

        return redirect(request.get_full_path())

    checked_ok.short_description = _("Checking is O.K.")

    def truncated_desc(self, obj):
        if len(obj.description) <= Error.TRUNCATED_DESC_LEN:
            return obj.description
        else:
            return obj.description[:Error.TRUNCATED_DESC_LEN] + ' ...'

    truncated_desc.short_description = _("Truncated description")
    truncated_desc.admin_order_field = 'description'

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return Error.objects.scope(request.user.userprofile)


@admin.register(FaultDefinition)
class FaultDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'enabled',
        'list_included_attributes', 'list_excluded_attributes',
        'list_users'
    )
    list_filter = ('enabled', 'users',)
    search_fields = ('name',)
    filter_horizontal = ('included_attributes',)

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'enabled', 'language', 'code')
        }),
        (_('Attributes'), {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('included_attributes', 'excluded_attributes')
        }),
        (_('Users'), {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('users',)
        }),
    )

    def get_queryset(self, request):
        qs = Attribute.objects.scope(request.user.userprofile)

        return FaultDefinition.objects.scope(
            request.user.userprofile
        ).prefetch_related(
            Prefetch('included_attributes', queryset=qs),
            Prefetch('excluded_attributes', queryset=qs),
            'included_attributes__property_att',
            'excluded_attributes__property_att',
            'users',
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
                Q(fault_definition__users__id=me) |
                Q(fault_definition__users=None)
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
        # 'list_users'  # performance improvement
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
        for item in queryset:
            item.checked_ok()

        return redirect(request.get_full_path())

    checked_ok.short_description = _("Checking is O.K.")

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return Fault.objects.scope(request.user.userprofile)


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
    exclude = ('computer',)
    actions = None

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return Migration.objects.scope(request.user.userprofile)


@admin.register(Synchronization)
class SynchronizationAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'project')
    list_display_links = ('__str__',)
    list_filter = ('created_at', 'project', 'pms_status_ok')
    search_fields = add_computer_search_fields(['created_at', 'user__name'])
    readonly_fields = (
        'computer', 'user', 'project', 'created_at',
        'start_date', 'consumer', 'pms_status_ok'
    )
    exclude = ('computer',)
    actions = None

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return Synchronization.objects.scope(request.user.userprofile)


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

    def get_queryset(self, request):
        return StatusLog.objects.scope(request.user.userprofile)
