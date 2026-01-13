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
User admin classes (UserProfile).
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ..forms import UserProfileForm
from ..models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    form = UserProfileForm
    list_display = ('username', 'first_name', 'last_name', 'domain_preference')
    ordering = ('username',)
    search_fields = ('username', 'first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_login')
    actions = ['activate_users']

    fieldsets = (
        (
            _('General'),
            {
                'fields': (
                    'username',
                    'first_name',
                    'last_name',
                    'email',
                    'date_joined',
                    'last_login',
                ),
            },
        ),
        (
            _('Authorizations'),
            {
                'fields': (
                    'is_active',
                    'is_superuser',
                    'is_staff',
                    'groups',
                    'user_permissions',
                    'domains',
                ),
            },
        ),
        (
            _('Preferences'),
            {
                'fields': (
                    'domain_preference',
                    'scope_preference',
                ),
            },
        ),
    )

    def activate_users(self, request, queryset):
        cnt = queryset.filter(is_active=False).update(is_active=True)
        self.message_user(request, f'Activated {cnt} users.')

    activate_users.short_description = _('Activate Users')

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.has_perm('auth.change_user'):
            del actions['activate_users']

        return actions

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        is_superuser = request.user.is_superuser
        disabled_fields = set()

        if not is_superuser:
            disabled_fields |= {
                'username',
                'is_superuser',
                'user_permissions',
            }

        # Prevent non-superusers from editing their own permissions
        if not is_superuser and obj is not None and obj == request.user:
            disabled_fields |= {
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            }

        for item in disabled_fields:
            if item in form.base_fields:
                form.base_fields[item].disabled = True

        return form
