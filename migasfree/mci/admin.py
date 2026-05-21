from django.contrib import admin
from django.db import models

from migasfree.core.models import ServerAttribute
from migasfree.mci.models import Build, Config, Flavour, Release


@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ('project', 'template_id', 'build_type', 'image_format', 'base_os')
    list_filter = ('build_type', 'image_format')
    search_fields = ('project__name', 'template_id')
    raw_id_fields = ('project',)

    formfield_overrides = {
        models.JSONField: {
            'widget': admin.widgets.AdminTextareaWidget(
                attrs={'rows': 15, 'cols': 80, 'style': 'font-family: monospace;'}
            )
        },
    }


@admin.register(Flavour)
class FlavourAdmin(admin.ModelAdmin):
    list_display = ('name', 'config', 'enabled', 'user')
    search_fields = ('name', 'config__project__name', 'tags__value', 'user')
    list_filter = ('enabled', 'keymap', 'timezone')
    raw_id_fields = ('config',)
    filter_horizontal = ('tags',)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'tags':
            kwargs['queryset'] = ServerAttribute.objects.filter(property_att__sort='server')
        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(Release)
class ReleaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'config', 'created_at')
    search_fields = ('name', 'config__project__name')
    raw_id_fields = ('config',)


@admin.register(Build)
class BuildAdmin(admin.ModelAdmin):
    list_display = ('release', 'flavour', 'status', 'started_at', 'finished_at')
    list_filter = ('status',)
    search_fields = ('release__name', 'flavour__name')
    raw_id_fields = ('release', 'flavour')
