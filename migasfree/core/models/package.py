# -*- coding: utf-8 -*-

# Copyright (c) 2015-2018 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2018 Alberto Gacías <alberto@migasfree.org>
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
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .project import Project
from .store import Store


class PackageManager(models.Manager):
    def create(self, fullname, name, version, architecture, project, store):
        target = Store.path(project.slug, store.slug)
        if not os.path.exists(target):
            os.makedirs(target)

        Package.handle_uploaded_file(
            fullname,
            os.path.join(target, fullname)
        )

        package = Package(
            fullname=fullname,
            name=name,
            version=version,
            architecture=architecture,
            project=project,
            store=store
        )
        package.save()

        return package


@python_2_unicode_compatible
class Package(models.Model):
    fullname = models.CharField(
        verbose_name=_('fullname'),
        max_length=170,
        null=False,
        unique=False
    )

    name = models.CharField(
        verbose_name=_('name'),
        max_length=100,
        null=False,
        blank=True,
        unique=False
    )

    version = models.CharField(
        verbose_name=_('version'),
        max_length=60,
        null=False,
        unique=False
    )

    architecture = models.CharField(
        verbose_name=_('architecture'),
        max_length=10,
        null=False,
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_("project")
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        null=True,
        verbose_name=_("store")
    )

    objects = PackageManager()

    @staticmethod
    def normalized_name(package_name):
        name = None
        version = None
        architecture = None

        # name_version_architecture.ext convention
        try:
            name, version, architecture = package_name.split('_')
        except ValueError:
            if package_name.count('_') > 2:
                slices = package_name.split('_', 1)
                name = slices[0]
                version, architecture = slices[1].rsplit('_', 1)

        architecture = architecture.split('.')[0]

        return name, version, architecture

    @staticmethod
    def handle_uploaded_file(f, target):
        path = os.path.dirname(target)
        if not os.path.isdir(path):
            os.makedirs(path)

        with open(target, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

    @staticmethod
    def orphan_count():
        return Package.objects.filter(deployment__id=None).count()

    @staticmethod
    def path(project_name, store_name, fullname):
        return os.path.join(Store.path(project_name, store_name), fullname)

    @staticmethod
    def delete_from_store(path):
        if os.path.exists(path):
            try:
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path, ignore_errors=True)
            except OSError:
                pass

    def create_dir(self):
        path = Store.path(self.project.slug, self.store.slug)
        if not os.path.exists(path):
            os.makedirs(path)

    def update_store(self, store):
        if self.store != store:
            previous_store = self.store.slug
            self.store = store
            self.save()

            shutil.move(
                self.path(self.project.slug, previous_store, self.name),
                self.path(self.project.slug, self.store, self.name)
            )

    def clean(self):
        super(Package, self).clean()

        if not hasattr(self, 'project'):
            return False

        if self.store.project.id != self.project.id:
            raise ValidationError(_('Store must belong to the project'))

        queryset = Package.objects.filter(
            fullname=self.fullname,
            project__id=self.project.id
        ).filter(~models.Q(id=self.id))
        if queryset.exists():
            raise ValidationError(_('Duplicated fullname at project'))

    def save(self, *args, **kwargs):
        self.create_dir()
        super(Package, self).save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        from migasfree.client.models import PackageHistory
        if PackageHistory.objects.filter(package__id=self.pk).exists():
            self.store = None
            self.save()
        else:
            super(Package, self).delete(using=using, keep_parents=keep_parents)

    def __str__(self):
        # return _('%s at project %s') % (self.fullname, self.project.name)
        return self.fullname

    class Meta:
        app_label = 'core'
        verbose_name = _('Package')
        verbose_name_plural = _('Packages')
        unique_together = (('fullname', 'project'),)


@receiver(pre_delete, sender=Package)
def delete_package(sender, instance, **kwargs):
    from .. import tasks
    from .deployment import Deployment

    path = Package.path(
        instance.project.slug,
        instance.store.slug,
        instance.fullname
    )
    Package.delete_from_store(path)

    queryset = Deployment.objects.filter(
        available_packages__in=[instance],
        enabled=True
    )
    for deploy in queryset:
        deploy.available_packages.remove(instance)
        tasks.create_repository_metadata.delay(deploy.id)
