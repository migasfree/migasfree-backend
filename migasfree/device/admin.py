# -*- coding: utf-8 -*-

# Copyright (c) 2015-2020 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2020 Alberto Gacías <alberto@migasfree.org>
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

from django import forms
from django.contrib import admin
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _

from migasfree.core.models import Attribute
from .models import (
    Type, Feature, Manufacturer, Connection,
    Driver, Logical, Model, Device
)


@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'device_type', 'fields')
    list_select_related = ('device_type',)
    search_fields = ('name',)
    ordering = ('device_type__name', 'name', 'fields')


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'model', 'project', 'feature')
    list_display_links = ('__str__',)
    list_filter = ('project', 'model')
    search_fields = ('name',)


class LogicalForm(forms.ModelForm):
    class Meta:
        model = Logical
        fields = '__all__'


@admin.register(Logical)
class LogicalAdmin(admin.ModelAdmin):
    form = LogicalForm
    fields = ('device', 'feature', 'alternative_feature_name', 'attributes')
    list_select_related = ('device', 'feature',)
    list_display = ('device', 'feature')
    list_filter = ('device__model', 'feature')
    ordering = ('device__name', 'feature__name')
    search_fields = (
        'id',
        'device__name',
        'device__model__name',
        'device__model__manufacturer__name',
        'feature__name',
    )

    def get_queryset(self, request):
        qs = Attribute.objects.scope(request.user.userprofile)

        return super(LogicalAdmin, self).get_queryset(
            request
        ).prefetch_related(
            Prefetch('attributes', queryset=qs),
            'attributes__property_att',
        )


class LogicalInline(admin.TabularInline):
    model = Logical
    form = LogicalForm
    fields = ('feature', 'alternative_feature_name', 'attributes')
    extra = 0

    def get_queryset(self, request):
        qs = Attribute.objects.scope(request.user.userprofile)
        return super(LogicalInline, self).get_queryset(
            request
        ).prefetch_related(
            Prefetch('attributes', queryset=qs),
            'attributes__property_att',
        )


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'model', 'connection', 'computers')
    list_filter = ('model', 'model__manufacturer')
    search_fields = ('name', 'model__name', 'model__manufacturer__name', 'data')
    fields = ('name', 'model', 'connection', 'available_for_attributes', 'data')
    ordering = ('name',)

    inlines = [LogicalInline]

    def computers(self, obj):
        related_objects = obj.related_objects('computer', self.user.userprofile)
        if related_objects:
            return related_objects.count()

        return 0

    computers.short_description = _('Computers')

    def get_queryset(self, request):
        self.user = request.user
        qs = Attribute.objects.scope(request.user.userprofile)

        return super(DeviceAdmin, self).get_queryset(
            request
        ).select_related(
            'connection', 'connection__device_type',
            'model', 'model__manufacturer', 'model__device_type',
        ).prefetch_related(
            Prefetch('logical_set__attributes', queryset=qs),
            'logical_set__attributes__property_att',
            Prefetch('available_for_attributes', queryset=qs),
            'logical_set'
        )

    def save_related(self, request, form, formsets, change):
        super(DeviceAdmin, self).save_related(request, form, formsets, change)
        device = form.instance

        for feature in Feature.objects.filter(
            driver__model__id=device.model.id
        ).distinct():
            if Logical.objects.filter(
                device__id=device.id,
                feature=feature
            ).count() == 0:
                device.logical_set.create(
                    device=device,
                    feature=feature
                )


class DriverInline(admin.TabularInline):
    model = Driver
    fields = ('project', 'feature', 'name', 'packages_to_install')
    ordering = ('project', 'feature')
    extra = 1


@admin.register(Model)
class ModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'manufacturer', 'device_type')
    list_filter = ('device_type', 'manufacturer')
    ordering = ('device_type__name', 'manufacturer__name', 'name')
    search_fields = (
        'name',
        'manufacturer__name',
        'connections__devicetype__name'
    )
    inlines = [DriverInline]
