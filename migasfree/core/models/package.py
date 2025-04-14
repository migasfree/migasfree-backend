# -*- coding: utf-8 -*-

# Copyright (c) 2015-2025 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2025 Alberto Gacías <alberto@migasfree.org>
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
import re
import shutil

from importlib import import_module

from django.db import models
from django.db.models.aggregates import Count
from django.db.models.signals import pre_delete, post_save
from django.conf import settings
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from ..pms import get_available_pms, get_available_extensions

from .migas_link import MigasLink
from .project import Project
from .store import Store


class DomainPackageManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('project', 'store')

    def scope(self, user):
        qs = self.get_queryset()
        if user and not user.is_view_all():
            qs = qs.filter(project__in=user.get_projects())

        return qs


class PackageManager(DomainPackageManager):
    def create(self, fullname, name, version, architecture, project, store, file_=None):
        if store and file_:
            Package.handle_uploaded_file(
                file_,
                os.path.join(Store.path(project.slug, store.slug), fullname)
            )

        if Package.objects.filter(fullname=fullname, project=project).exists() and store and file_:
            package = Package.objects.get(fullname=fullname, project=project)
            package.store = store
        else:
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

    def by_project(self, project_id):
        return self.get_queryset().filter(project__id=project_id)


class Package(models.Model, MigasLink):
    fullname = models.CharField(
        verbose_name=_('fullname'),
        max_length=170,
        null=False,
        unique=False,
        db_comment='package fullname (name + version + architecture + extension)',
    )

    name = models.CharField(
        verbose_name=_('name'),
        max_length=100,
        null=False,
        blank=True,
        unique=False,
        db_comment='package name',
    )

    version = models.CharField(
        verbose_name=_('version'),
        max_length=60,
        null=False,
        unique=False,
        db_comment='package version',
    )

    architecture = models.CharField(
        verbose_name=_('architecture'),
        max_length=10,
        null=False,
        db_comment='package architecture',
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_('project'),
        db_comment='related project',
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        null=True,
        verbose_name=_('store'),
        db_comment='related store',
    )

    objects = PackageManager()

    @staticmethod
    def normalized_name(filename):
        extensions = get_available_extensions()
        for ext in extensions:
            if filename.endswith(ext):
                base = filename[:-len(ext)].rstrip('_.-')  # remove possible separators after extension
                break
            else:
                base = filename

        match = re.match(r'^(.*?)[-_\.](?=\d|v\d)(.*)[-_.]([a-zA-Z][a-zA-Z0-9_]*)$', base)
        if match:
            name, version, arch = match.groups()
            return (name, version, arch or '')
        else:
            return (base, '', '')

    @staticmethod
    def handle_uploaded_file(f, target):
        path = os.path.dirname(target)
        if not os.path.isdir(path):
            os.makedirs(path)

        with open(target, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

    @staticmethod
    def orphan_count(user=None):
        if not user:
            return Package.objects.filter(
                deployment__isnull=True,
                store__isnull=False,
                packageset__isnull=True
            ).count()

        return Package.objects.scope(user).filter(
            deployment__isnull=True,
            store__isnull=False,
            packageset__isnull=True
        ).count()

    def pms(self):
        available_pms = dict(get_available_pms())
        mod = import_module(
            f'migasfree.core.pms.{available_pms.get(self.project.pms)}'
        )
        return getattr(mod, self.project.pms.capitalize())()

    def url(self):
        if not self.store:
            return ''

        return '{}{}/{}/{}/{}'.format(
            settings.MEDIA_URL,
            self.project.slug,
            settings.MIGASFREE_STORE_TRAILING_PATH,
            self.store.slug,
            self.fullname
        )

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

    @staticmethod
    def by_store(user):
        total = Package.objects.scope(user).count()

        stores = list(Package.objects.scope(user).values(
            'project__id', 'store__id', 'store__name'
        ).annotate(
            count=Count('id')
        ).order_by('project__id', 'store__name', '-count'))

        projects = list(Package.objects.scope(user).values(
            'project__id', 'project__name'
        ).annotate(
            count=Count('id')
        ).order_by('project__id', '-count'))

        return {
            'total': total,
            'inner': projects,
            'outer': stores,
        }

    def create_dir(self):
        if self.store:
            path = Store.path(self.project.slug, self.store.slug)
            if not os.path.exists(path):
                os.makedirs(path)

    def update_store(self, store):
        previous_store = None
        if self.store != store:
            if self.store:
                previous_store = self.store.slug

            self.store = store
            self.save()

            if previous_store:
                shutil.move(
                    self.path(self.project.slug, previous_store, self.name),
                    self.path(self.project.slug, self.store, self.name)
                )

    def update_package_data(self, name, version, architecture):
        self.name = name
        self.version = version
        self.architecture = architecture
        self.save()

    def clean(self):
        super().clean()

        if not hasattr(self, 'project'):
            return False

        if self.store and self.store.project.id != self.project_id:
            raise ValidationError(_('Store must belong to the project'))

        queryset = Package.objects.filter(
            fullname=self.fullname,
            project__id=self.project_id
        ).filter(~models.Q(id=self.id))
        if queryset.exists():
            raise ValidationError(_('Duplicated fullname at project'))

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.create_dir()
        super().save(force_insert, force_update, using, update_fields)

    def delete(self, using=None, keep_parents=False):
        from ...client.models import PackageHistory

        if PackageHistory.objects.filter(package__id=self.pk).exists():
            self.store = None
            self.save()
            return 0, {}

        return super().delete(using=using, keep_parents=keep_parents)

    def __str__(self):
        # return _('%s at project %s') % (self.fullname, self.project.name)
        return self.fullname

    class Meta:
        app_label = 'core'
        verbose_name = _('Package')
        verbose_name_plural = _('Packages')
        unique_together = (('fullname', 'project'),)
        db_table_comment = 'software package details: contains the name, version,'
        ' architecture, related project and store'


def _update_deployments(instance, delete=False):
    from ..pms import tasks
    from .deployment import Deployment

    queryset = Deployment.objects.filter(available_packages__in=[instance])
    for deploy in queryset:
        if delete:
            deploy.available_packages.remove(instance)
        tasks.create_repository_metadata.apply_async(
            queue=f'pms-{deploy.pms().name}',
            kwargs={'deployment_id': deploy.id}
        )


@receiver(post_save, sender=Package)
def save_package(sender, instance, **kwargs):
    if instance.store:
        _update_deployments(instance)


@receiver(pre_delete, sender=Package)
def delete_package(sender, instance, **kwargs):
    if not instance.store:
        return

    path = Package.path(
        instance.project.slug,
        instance.store.slug,
        instance.fullname
    )
    Package.delete_from_store(path)
    _update_deployments(instance, delete=True)
