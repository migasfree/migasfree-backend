# -*- coding: utf-8 -*-

# Copyright (c) 2015 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015 Alberto Gacías <alberto@migasfree.org>
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
from django import forms
from django.db import models
from django.db.models import Q

from .models import (
    Type, Feature, Manufacturer, Connection,
    Driver, Logical, Model, Device
)

admin.site.register(Type)
admin.site.register(Feature)
admin.site.register(Manufacturer)


class ConnectionAdmin(admin.ModelAdmin):
    list_select_related = ('device_type',)

admin.site.register(Connection, ConnectionAdmin)


class DriverAdmin(admin.ModelAdmin):
    list_display = ('id', 'model', 'project', 'feature')

admin.site.register(Driver, DriverAdmin)


class LogicalForm(forms.ModelForm):
    """
    x = make_ajax_form(Computer, {'devices_logical': 'computer'})

    computers = x.logical
    computers.label = _('Computers')

    def __init__(self, *args, **kwargs):
        super(LogicalForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            lst = []
            for computer in self.instance.computer_set.all():
                lst.append(computer.id)
            self.fields['computers'].initial = lst

    def save(self, commit=True):
        instance = forms.ModelForm.save(self, False)
        old_save_m2m = self.save_m2m

        def save_m2m():
            old_save_m2m()
            instance.computer_set.clear()
            for computer in self.cleaned_data['computers']:
                instance.computer_set.add(computer)

        self.save_m2m = save_m2m
        if commit:
            instance.save()
            self.save_m2m()
        return instance
    """

    class Meta:
        model = Logical


class LogicalAdmin(admin.ModelAdmin):
    form = LogicalForm
    fields = ("device", "feature")  #, "computers")
    list_select_related = ('device', 'feature',)
    list_display = ('device', 'feature')

admin.site.register(Logical, LogicalAdmin)


class LogicalInline(admin.TabularInline):
    model = Logical
    form = LogicalForm
    fields = ("feature", )  # "computers")
    extra = 0


class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'model')
    list_filter = ('model',)
    search_fields = ('name', 'model__name', 'model__manufacturer__name')
    fields = ('name', 'model', 'connection', 'data')

    inlines = [LogicalInline]

    def save_related(self, request, form, formsets, change):
        super(type(self), self).save_related(request, form, formsets, change)
        device = form.instance

        for feature in Feature.objects.filter(
            driver__model__id=device.model.id
        ).distinct():
            if Logical.objects.filter(
                Q(device__id=device.id) & Q(feature=feature)
            ).count() == 0:
                logical = device.logical_set.create(
                    device=device,
                    feature=feature
                )
                logical.save()

admin.site.register(Device, DeviceAdmin)


class DriverInline(admin.TabularInline):
    model = Driver
    fields = ('project', 'feature', 'name', 'packages_to_install')
    ordering = ['project', 'feature']
    extra = 1


class ModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'manufacturer', 'device_type')
    list_filter = ('device_type', 'manufacturer')
    search_fields = (
        'name',
        'manufacturer__name',
        'connections__devicetype__name'
    )
    inlines = [DriverInline]

admin.site.register(Model, ModelAdmin)
