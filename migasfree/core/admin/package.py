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
Package admin classes (Package, PackageSet).
"""

import os

from django.contrib import admin
from django.db.models import Prefetch

from ..forms import PackageForm
from ..models import Deployment, Package, PackageSet, Store


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    form = PackageForm

    list_display = ('name', 'version', 'architecture', 'project', 'store')
    list_filter = ('project__platform', 'project__name', 'store', 'deployment')
    list_select_related = (
        'project',
        'store',
    )
    search_fields = (
        'name',
        'store__name',
    )
    ordering = ('name',)

    def get_queryset(self, request):
        return Package.objects.scope(request.user.userprofile).prefetch_related(
            Prefetch('deployment_set', queryset=Deployment.objects.scope(request.user.userprofile))
        )

    def save_model(self, request, obj, form, change):
        package_file = request.FILES['package_file']
        if obj.id:
            if obj.store and package_file:
                Package.handle_uploaded_file(
                    package_file, os.path.join(Store.path(obj.project.slug, obj.store.slug), obj.fullname)
                )
            super().save_model(request, obj, form, change)
        else:
            Package.objects.create(
                fullname=obj.fullname,
                project=obj.project,
                name=obj.name,
                version=obj.version,
                architecture=obj.architecture,
                store=obj.store,
                file_=package_file,
            )


@admin.register(PackageSet)
class PackageSetAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    ordering = ('name',)

    def get_queryset(self, request):
        return PackageSet.objects.scope(request.user.userprofile)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'packages':
            kwargs['queryset'] = Package.objects.filter(store__isnull=False)

            return db_field.formfield(**kwargs)

        return super().formfield_for_manytomany(db_field, request, **kwargs)
