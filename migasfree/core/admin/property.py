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
Property admin classes (ClientProperty, ServerProperty, Singularity).
"""

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.db.models import Prefetch

from ..forms import ClientPropertyForm
from ..models import (
    Attribute,
    ClientProperty,
    Property,
    ServerProperty,
    Singularity,
)


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
    search_fields = (
        'name',
        'prefix',
    )
    fields = (
        'prefix',
        'name',
        'enabled',
        'language',
        'code',
        'kind',
    )


class ServerPropertyFilter(SimpleListFilter):
    title = 'Server Property'
    parameter_name = 'Server Property'

    def lookups(self, request, model_admin):
        return [(c.id, c.name) for c in Property.objects.filter(sort='server')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(id__exact=self.value())

        return queryset.filter(sort='server')


@admin.register(ServerProperty)
class ServerPropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'prefix', 'enabled', 'kind')
    fields = ('prefix', 'name', 'kind', 'enabled')
    list_filter = (ServerPropertyFilter,)


@admin.register(Singularity)
class SingularityAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'enabled',
        'language',
        'property_att',
        'priority',
        'list_included_attributes',
        'list_excluded_attributes',
    )
    list_filter = ('enabled',)
    ordering = ('property_att__name', '-priority')
    search_fields = ('name', 'property_att__name', 'property_att__prefix')
    filter_horizontal = ('included_attributes', 'excluded_attributes')

    def get_queryset(self, request):
        qs = Attribute.objects.scope(request.user.userprofile)

        return Singularity.objects.scope(request.user.userprofile).prefetch_related(
            Prefetch('included_attributes', queryset=qs),
            Prefetch('excluded_attributes', queryset=qs),
            'included_attributes__property_att',
            'excluded_attributes__property_att',
        )
