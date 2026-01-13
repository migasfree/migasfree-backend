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
Schedule admin classes (Schedule, ScheduleDelay).
"""

from django.contrib import admin
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _

from ..models import Attribute, Schedule, ScheduleDelay


class ScheduleDelayLine(admin.TabularInline):
    model = ScheduleDelay
    fields = ('delay', 'attributes', 'computers', 'duration')
    readonly_fields = ('computers',)
    extra = 0
    ordering = ('delay',)

    def computers(self, obj):
        related_objects = obj.related_objects('computer', self.request.user.userprofile)
        return related_objects.count() if related_objects else 0

    computers.short_description = _('Computers')

    def get_queryset(self, request):
        self.request = request
        qs = Attribute.objects.scope(request.user.userprofile)

        return ScheduleDelay.objects.scope(request.user.userprofile).prefetch_related(
            Prefetch('attributes', queryset=qs), 'attributes__property_att', 'schedule'
        )


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'delays_count')
    search_fields = ('name', 'description')
    ordering = ('name',)
    inlines = [
        ScheduleDelayLine,
    ]
    extra = 0

    fieldsets = (('', {'fields': ('name', 'description')}),)
