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
Project admin classes (Platform, Project, Store).
"""

from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin

from ..forms import StoreForm
from ..models import Platform, Project, Store
from ..resources import ProjectResource
from ..validators import validate_no_spaces

admin.site.register(Platform)


@admin.register(Project)
class ProjectAdmin(ImportExportActionModelAdmin):
    resource_class = ProjectResource
    list_display = ('name', 'platform', 'pms', 'auto_register_computers')
    list_filter = (
        'platform',
        'pms',
    )
    list_select_related = ('platform',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    def get_queryset(self, request):
        return Project.objects.scope(request.user.userprofile)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        form.base_fields['name'].validators.append(validate_no_spaces)

        return form


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    form = StoreForm
    list_display = ('name', 'project')
    list_filter = ('project__name',)
    search_fields = ('name',)
    read_only_fields = ('slug',)
    fields = ('name', 'project')

    def get_queryset(self, request):
        return Store.objects.scope(request.user.userprofile)
