# -*- coding: utf-8 -*-

# Copyright (c) 2017-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2017-2021 Alberto Gacías <alberto@migasfree.org>
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

from django.contrib import admin
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _

from ..core.models import Attribute

from .models import (
    Category, Application, PackagesByProject,
    Policy, PolicyGroup,
)


@admin.register(PackagesByProject)
class PackagesByProjectAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'application', 'project', 'packages_to_install'
    )
    list_display_links = ('id',)
    list_filter = ('application__name',)
    search_fields = ('application__name', 'packages_to_install')


class PackagesByProjectLine(admin.TabularInline):
    model = PackagesByProject
    fields = ('project', 'packages_to_install')
    ordering = ('project',)
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields['project'].widget.can_change_related = False
        formset.form.base_fields['project'].widget.can_add_related = False

        return formset

    def get_queryset(self, request):
        return PackagesByProject.objects.scope(request.user.userprofile)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ('name',)

    def __str__(self):
        return self.name


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'score', 'level', 'category',)
    list_filter = ('level', 'category')
    ordering = ('name',)
    fields = (
        'name', 'category', 'level',
        'score', 'icon', 'available_for_attributes', 'description'
    )
    search_fields = ('name', 'description')

    inlines = [PackagesByProjectLine]
    extra = 0

    def get_queryset(self, request):
        qs = Attribute.objects.scope(request.user.userprofile)

        return super().get_queryset(
            request
        ).prefetch_related(
            Prefetch('available_for_attributes', queryset=qs)
        )

    def __str__(self):
        return self.name


@admin.register(PolicyGroup)
class PolicyGroupAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'policy', 'priority',
    )
    list_display_links = ('id',)
    list_filter = ('policy__name',)
    search_fields = (
        'policy__name', 'included_attributes__value',
        'excluded_attributes__value'
    )

    def get_queryset(self, request):
        qs = Attribute.objects.scope(request.user.userprofile)

        return super().get_queryset(
            request
        ).prefetch_related(
            Prefetch('included_attributes', queryset=qs),
            'included_attributes__property_att',
            Prefetch('excluded_attributes', queryset=qs),
            'excluded_attributes__property_att'
        )


class PolicyGroupLine(admin.TabularInline):
    model = PolicyGroup
    fields = (
        'priority', 'included_attributes',
        'excluded_attributes', 'applications'
    )
    ordering = ('priority',)
    extra = 0

    def get_queryset(self, request):
        qs = Attribute.objects.scope(request.user.userprofile)

        return super().get_queryset(
            request
        ).prefetch_related(
            Prefetch('included_attributes', queryset=qs),
            'included_attributes__property_att',
            Prefetch('excluded_attributes', queryset=qs),
            'excluded_attributes__property_att'
        )


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'enabled', 'exclusive',
    )
    list_filter = ('enabled', 'exclusive')
    list_display_links = ('name',)
    search_fields = (
        'name', 'included_attributes__value', 'excluded_attributes__value'
    )
    fieldsets = (
        (_('General'), {
            'fields': (
                'name',
                'comment',
                'enabled',
                'exclusive',
            )
        }),
        (_('Application Area'), {
            'fields': (
                'included_attributes',
                'excluded_attributes',
            )
        }),
    )
    inlines = [PolicyGroupLine]
    extra = 0

    def get_queryset(self, request):
        qs = Attribute.objects.scope(request.user.userprofile)

        return super().get_queryset(
            request
        ).prefetch_related(
            Prefetch('included_attributes', queryset=qs),
            'included_attributes__property_att',
            Prefetch('excluded_attributes', queryset=qs),
            'excluded_attributes__property_att'
        )
