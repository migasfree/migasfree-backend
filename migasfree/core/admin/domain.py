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
Domain admin classes (Domain, Scope).
"""

from django.contrib import admin
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _

from ..forms import DomainForm, ScopeForm
from ..models import Attribute, Domain, Scope, UserProfile


@admin.register(Scope)
class ScopeAdmin(admin.ModelAdmin):
    form = ScopeForm
    list_display = ('name', 'domain')
    ordering = ('name',)
    search_fields = ('name',)
    fieldsets = (
        (
            _('General'),
            {
                'fields': ('name', 'domain'),
            },
        ),
        (
            _('Attributes'),
            {
                'fields': (
                    'included_attributes',
                    'excluded_attributes',
                ),
            },
        ),
        (
            '',
            {
                'fields': ('user',),
                'classes': ['hidden'],
            },
        ),
    )

    def get_queryset(self, request):
        qs = Attribute.objects.scope(request.user.userprofile)

        return Scope.objects.scope(request.user.userprofile).prefetch_related(
            Prefetch('included_attributes', queryset=qs),
            'included_attributes__property_att',
            Prefetch('excluded_attributes', queryset=qs),
            'excluded_attributes__property_att',
        )


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    form = DomainForm
    list_display = ('name',)
    ordering = ('name',)
    search_fields = ('name',)
    fieldsets = (
        (
            _('General'),
            {
                'fields': (
                    'name',
                    'comment',
                    'users',
                ),
            },
        ),
        (
            _('Attributes'),
            {
                'fields': (
                    'included_attributes',
                    'excluded_attributes',
                ),
            },
        ),
        (
            _('Available tags'),
            {
                'fields': ('tags',),
            },
        ),
    )

    def get_queryset(self, request):
        user_profile = UserProfile.objects.get(id=request.user.id)
        user_profile.update_scope(0)

        return super().get_queryset(request)
