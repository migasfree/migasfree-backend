# -*- coding: utf-8 -*-

# Copyright (c) 2017-2022 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2017-2022 Alberto Gacías <alberto@migasfree.org>
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

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from markdownx.models import MarkdownxField

from ..core.models import Project, Attribute, MigasLink
from ..utils import to_list

_UNSAVED_IMAGEFIELD = 'unsaved_imagefield'


class DomainPackagesByProjectManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related('project')

    def scope(self, user):
        qs = self.get_queryset()
        if not user.is_view_all():
            qs = qs.filter(project__in=user.get_projects())

        return qs


class PackagesByProjectManager(DomainPackagesByProjectManager):
    def create(self, application, project, packages_to_install):
        obj = PackagesByProject()
        obj.application = application
        obj.project = project
        obj.packages_to_install = packages_to_install
        obj.save()

        return obj


class MediaFileSystemStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        if max_length and len(name) > max_length:
            raise Exception(_("name's length is greater than max length"))

        return name

    def _save(self, name, content):
        if self.exists(name):
            os.remove(os.path.join(settings.MIGASFREE_PUBLIC_DIR, name))

        return super()._save(name, content)


def upload_path_handler(instance, filename):
    _, ext = os.path.splitext(filename)
    return f'catalog_icons/app_{instance.pk}{ext}'


class Category(models.Model, MigasLink):
    name = models.CharField(
        verbose_name=_('name'),
        max_length=50,
        unique=True
    )

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'app_catalog'
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')


class Application(models.Model, MigasLink):
    LEVELS = (
        ('U', _('User')),
        ('A', _('Admin')),
    )

    name = models.CharField(
        verbose_name=_('name'),
        max_length=50,
        unique=True
    )

    description = MarkdownxField(
        verbose_name=_('description'),
        blank=True,
        help_text=_('markdown syntax allowed')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('date'))

    score = models.IntegerField(
        verbose_name=_('score'),
        default=1,
        choices=((1, 1), (2, 2), (3, 3), (4, 4), (5, 5)),
        help_text=_('Relevance to the organization')
    )

    icon = models.ImageField(
        verbose_name=_('icon'),
        upload_to=upload_path_handler,
        storage=MediaFileSystemStorage(),
        null=True
    )

    level = models.CharField(
        verbose_name=_('level'),
        max_length=1,
        default='U',
        choices=LEVELS
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name=_('category')
    )

    available_for_attributes = models.ManyToManyField(
        Attribute,
        blank=True,
        verbose_name=_('available for attributes')
    )

    @staticmethod
    def group_by_category():
        return Application.objects.values(
            'category__id', 'category__name'
        ).annotate(
            count=models.aggregates.Count('category__id')
        ).order_by('-count')

    @staticmethod
    def group_by_level():
        return Application.objects.values(
            'level',
        ).annotate(
            count=models.aggregates.Count('level')
        ).order_by('-count')

    @staticmethod
    def group_by_project():
        return Application.objects.values(
            'packages_by_project__project__name',
            'packages_by_project__project__id'
        ).annotate(
            count=models.aggregates.Count('id', distinct=True)
        ).order_by('packages_by_project__project__name')

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'app_catalog'
        verbose_name = _('Application')
        verbose_name_plural = _('Applications')


class PackagesByProject(models.Model, MigasLink):
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        verbose_name=_('application'),
        related_name='packages_by_project'
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_('project')
    )

    packages_to_install = models.TextField(
        verbose_name=_('packages to install'),
        blank=True,
    )

    objects = PackagesByProjectManager()

    def __str__(self):
        return f'{self.application}@{self.project}'

    class Meta:
        app_label = 'app_catalog'
        verbose_name = _('Packages by Project')
        verbose_name_plural = _('Packages by Projects')
        unique_together = (('application', 'project'),)
        ordering = ['application__id', 'project__name']


class Policy(models.Model, MigasLink):
    name = models.CharField(
        verbose_name=_('name'),
        max_length=50
    )

    enabled = models.BooleanField(
        verbose_name=_('enabled'),
        default=True,
        help_text=_("if you uncheck this field, the policy is disabled for"
                    " all computers.")
    )

    exclusive = models.BooleanField(
        verbose_name=_('exclusive'),
        default=True,
    )

    comment = models.TextField(
        verbose_name=_('comment'),
        null=True,
        blank=True
    )

    included_attributes = models.ManyToManyField(
        Attribute,
        related_name='policy_included',
        blank=True,
        verbose_name=_('included attributes'),
    )

    excluded_attributes = models.ManyToManyField(
        Attribute,
        related_name='policy_excluded',
        blank=True,
        verbose_name=_('excluded attributes'),
    )

    def __str__(self):
        return self.name

    @staticmethod
    def belongs(computer, attributes):
        for attribute in attributes:
            if attribute.id == 1 or \
                    attribute in computer.sync_attributes.all():
                return True

        return False

    @staticmethod
    def belongs_excluding(computer, included_attributes, excluded_attributes):
        if Policy.belongs(computer, included_attributes) and \
                not Policy.belongs(computer, excluded_attributes):
            return True

        return False

    @staticmethod
    def get_packages_to_remove(group, project_id=0):
        _packages = []
        for item in PolicyGroup.objects.filter(policy=group.policy).exclude(id=group.id):
            for pkgs in item.applications.filter(
                packages_by_project__project__id=project_id
            ).values_list(
                'packages_by_project__packages_to_install',
                flat=True
            ):
                for pkg in to_list(pkgs):
                    _packages.append({
                        'package': pkg,
                        'name': group.policy.name,
                        'id': group.policy.id
                    })

        return _packages

    @staticmethod
    def get_packages(computer):
        to_install = []
        to_remove = []

        for policy in Policy.objects.filter(enabled=True):
            if policy.belongs_excluding(
                    computer,
                    policy.included_attributes.all(),
                    policy.excluded_attributes.all()
            ):
                for group in PolicyGroup.objects.filter(
                        policy=policy
                ).order_by('priority'):
                    if policy.belongs_excluding(
                            computer,
                            group.included_attributes.all(),
                            group.excluded_attributes.all()
                    ):
                        for pkgs in group.applications.filter(
                                packages_by_project__project__id=computer.project.id
                        ).values_list(
                            'packages_by_project__packages_to_install',
                            flat=True
                        ):
                            for item in to_list(pkgs):
                                to_install.append({
                                    'package': item,
                                    'name': policy.name,
                                    'id': policy.id
                                })

                        if policy.exclusive:
                            to_remove.extend(
                                policy.get_packages_to_remove(group, computer.project.id)
                            )
                        break

        return to_install, to_remove

    class Meta:
        app_label = 'app_catalog'
        verbose_name = _('Policy')
        verbose_name_plural = _('Policies')
        unique_together = ('name',)
        ordering = ['name']


class PolicyGroup(models.Model, MigasLink):
    priority = models.IntegerField(
        verbose_name=_('priority')
    )

    policy = models.ForeignKey(
        Policy,
        on_delete=models.CASCADE,
        verbose_name=_('policy')
    )

    included_attributes = models.ManyToManyField(
        Attribute,
        related_name='policygroup_included',
        blank=True,
        verbose_name=_('included attributes'),
    )

    excluded_attributes = models.ManyToManyField(
        Attribute,
        related_name='policygroup_excluded',
        blank=True,
        verbose_name=_('excluded attributes'),
    )

    applications = models.ManyToManyField(
        Application,
        blank=True,
        verbose_name=_('application'),
    )

    def __str__(self):
        return f'{self.policy.name} ({self.priority})'

    class Meta:
        app_label = 'app_catalog'
        verbose_name = _('Policy Group')
        verbose_name_plural = _('Policy Groups')
        unique_together = (('policy', 'priority'),)
        ordering = ['policy__name', 'priority']


@receiver(pre_save, sender=Application)
def pre_save_application(sender, instance, **kwargs):
    if not instance.pk and not hasattr(instance, _UNSAVED_IMAGEFIELD):
        setattr(instance, _UNSAVED_IMAGEFIELD, instance.icon)
        instance.icon = None


@receiver(post_save, sender=Application)
def post_save_application(sender, instance, created, **kwargs):
    if created and hasattr(instance, _UNSAVED_IMAGEFIELD):
        instance.icon = getattr(instance, _UNSAVED_IMAGEFIELD)
        instance.save()
        instance.__dict__.pop(_UNSAVED_IMAGEFIELD)
