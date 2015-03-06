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

import os
import shutil

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.db.models.signals import pre_delete
from django.dispatch import receiver

# from migasfree.utils import trans
from .project import Project
from .store import Store


class PackageManager(models.Manager):
    def create(self, name, project, store, file_list):
        target = os.path.join(
            settings.MIGASFREE_PUBLIC_DIR,
            project.slug,
            'stores',
            store.slug,
        )
        if len(file_list) > 1 or name != str(file_list[0]):
            target = os.path.join(target, name)

        if not os.path.exists(target):
            os.makedirs(target)

        for item in file_list:
            Package.handle_uploaded_file(
                item,
                os.path.join(target, str(item))
            )

        package = Package(
            name=name,
            project=project,
            store=store
        )
        package.save()
        return package


@python_2_unicode_compatible
class Package(models.Model):
    name = models.CharField(
        _("name"),
        max_length=100
    )

    project = models.ForeignKey(
        Project,
        verbose_name=_("project")
    )

    store = models.ForeignKey(
        Store,
        verbose_name=_("store")
    )

    objects = PackageManager()

    def clean(self):
        super(Package, self).clean()

        if self.store.project.id != self.project.id:
            raise ValidationError(_('Store must belong to the project'))

        queryset = Package.objects.filter(
            name=self.name
        ).filter(project__id=self.project.id)
        if queryset.exists():
            raise ValidationError(_('Duplicated name at project'))

    @staticmethod
    def handle_uploaded_file(f, target):
        with open(target, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

    @staticmethod
    def orphaned():
        return Package.objects.filter(repository__id=None).count()

    def create_dir(self):
        _path = os.path.join(
            settings.MIGASFREE_PUBLIC_DIR,
            self.project.slug,
            'stores',
            self.store.slug,
            self.name
        )
        if not os.path.exists(_path):
            os.makedirs(_path)

    def __str__(self):
        return _('%s at project %s') % (self.name, self.project.name)

    class Meta:
        app_label = 'core'
        verbose_name = _('Package/Set')
        verbose_name_plural = _('Packages/Sets')
        unique_together = (('name', 'project'),)


@receiver(pre_delete, sender=Package)
def delete_package(sender, instance, **kwargs):
    _path = os.path.join(
        settings.MIGASFREE_PUBLIC_DIR,
        instance.project.slug,
        'stores',
        instance.store.slug,
        instance.name
    )
    if os.path.exists(_path):
        try:
            if os.path.isfile(_path):
                os.remove(_path)
            else:
                shutil.rmtree(_path)
        except:
            pass
