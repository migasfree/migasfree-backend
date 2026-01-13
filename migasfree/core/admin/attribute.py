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
Attribute admin classes (ClientAttribute, ServerAttribute, AttributeSet).
"""

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.db.models import Count, Prefetch, Q
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportActionModelAdmin

from ...client.models import Computer
from ..models import (
    Attribute,
    AttributeSet,
    ClientAttribute,
    Property,
    ServerAttribute,
)
from ..resources import AttributeResource


class ClientAttributeFilter(SimpleListFilter):
    title = 'Client Attribute'
    parameter_name = 'Client Attribute'

    def lookups(self, request, model_admin):
        return [(c.id, c.name) for c in Property.objects.filter(Q(sort='client') | Q(sort='basic'))]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(property_att__id__exact=self.value())

        return queryset


@admin.register(ClientAttribute)
class ClientAttributeAdmin(ImportExportActionModelAdmin):
    list_display = ('id', 'property_att', 'value', 'description')
    list_select_related = ('property_att',)
    list_filter = (ClientAttributeFilter,)
    ordering = (
        'property_att',
        'value',
    )
    search_fields = ('value', 'description')
    readonly_fields = (
        'property_att',
        'value',
    )
    resource_class = AttributeResource

    def get_queryset(self, request):
        user = request.user.userprofile
        queryset = ClientAttribute.objects.scope(user)

        # Build computer filter for counting
        computer_filter = Q(computer__isnull=False)
        if user and not user.is_view_all():
            computers = user.get_computers()
            if computers:
                computer_filter &= Q(computer__id__in=computers)

        return queryset.annotate(total_computers=Count('computer', filter=computer_filter, distinct=True))


class ServerAttributeFilter(SimpleListFilter):
    title = 'Server Attribute'
    parameter_name = 'Server Attribute'

    def lookups(self, request, model_admin):
        return [(c.id, c.name) for c in Property.objects.filter(sort='server')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(property_att__id__exact=self.value())

        return queryset


@admin.register(ServerAttribute)
class ServerAttributeAdmin(ImportExportActionModelAdmin):
    list_display = ('value', 'description', 'property_att')
    fields = ('property_att', 'value', 'description', 'inflicted_computers')
    list_filter = (ServerAttributeFilter,)
    ordering = (
        'property_att',
        'value',
    )
    search_fields = ('value', 'description')
    readonly_fields = ('inflicted_computers',)
    resource_class = AttributeResource

    def get_queryset(self, request):
        user = request.user.userprofile
        queryset = ServerAttribute.objects.scope(user)

        # Build computer filter for counting
        computer_filter = Q(computer__isnull=False)
        if user and not user.is_view_all():
            computers = user.get_computers()
            if computers:
                computer_filter &= Q(computer__id__in=computers)

        return queryset.annotate(total_computers=Count('computer', filter=computer_filter, distinct=True))

    def inflicted_computers(self, obj):
        ret = [c.__str__() for c in Computer.productive.filter(sync_attributes__in=[obj.pk]).exclude(tags__in=[obj.pk])]

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

        return AttributeSet.objects.scope(request.user.userprofile).prefetch_related(
            Prefetch('included_attributes', queryset=qs),
            Prefetch('excluded_attributes', queryset=qs),
            'included_attributes__property_att',
            'excluded_attributes__property_att',
        )
