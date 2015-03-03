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
import datetime

from django.db import models
from django.template.defaultfilters import slugify
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.db.models import Q
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from migasfree.utils import time_horizon

from .project import Project
from .package import Package
from .attribute import Attribute
from .schedule import Schedule


@python_2_unicode_compatible
class Repository(models.Model):
    enabled = models.BooleanField(
        verbose_name=_('enabled'),
        default=True,
        help_text=_("if you uncheck this field, repository is disabled for all"
            " computers.")
    )

    name = models.CharField(
        max_length=50,
        verbose_name=_('name')
    )

    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name=_('slug')
    )

    project = models.ForeignKey(Project, verbose_name=_('project'))

    comment = models.TextField(
        verbose_name=_("comment"),
        null=True,
        blank=True
    )

    available_packages = models.ManyToManyField(
        Package,
        null=True,
        blank=True,
        verbose_name=_('available'),
        help_text=_('If a computer has installed one of these packages it will'
            ' be updated')
    )

    packages_to_install = models.TextField(
        verbose_name=_("To install"),
        null=True,
        blank=True,
        help_text=_('Mandatory packages to install each time')
    )

    packages_to_remove = models.TextField(
        verbose_name=_("To remove"),
        null=True,
        blank=True,
        help_text=_('Mandatory packages to remove each time')
    )

    included_attributes = models.ManyToManyField(
        Attribute,
        null=True,
        blank=True,
        verbose_name=_("included")
    )

    excluded_attributes = models.ManyToManyField(
        Attribute,
        related_name="ExcludeAttribute",
        null=True,
        blank=True,
        verbose_name=_("excluded")
    )

    schedule = models.ForeignKey(
        Schedule,
        verbose_name=_('schedule'),
        null=True,
        blank=True
    )

    start_date = models.DateField(
        default=datetime.date.today(),
        verbose_name=_('start date')
    )

    default_preincluded_packages = models.TextField(
        verbose_name=_("default pre-included packages"),
        null=True,
        blank=True
    )

    default_included_packages = models.TextField(
        verbose_name=_("default included packages"),
        null=True,
        blank=True
    )

    default_excluded_packages = models.TextField(
        verbose_name=_("default excluded packages"),
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)

        self.packages_to_install = self.packages_to_install.replace("\r\n", "\n")
        self.packages_to_remove = self.packages_to_remove.replace("\r\n", "\n")

        self.default_preincluded_packages = self.default_preincluded_packages.replace("\r\n", "\n")
        self.default_included_packages = self.default_included_packages.replace("\r\n", "\n")
        self.default_excluded_packages = self.default_excluded_packages.replace("\r\n", "\n")

        super(Repository, self).save(*args, **kwargs)

    #@shared_task(queue = 'repository')
    @staticmethod
    def remove_repository_metadata(repo_id, old_slug=''):
        _repo = Repository.objects.get(id=repo_id)

        if old_slug:
            _slug = old_slug
        else:
            _slug = _repo.slug

        exec('from migasfree.core.pms import %s' % _repo.project.pms)
        _pms = eval('%s.%s' % (
            _repo.project.pms,
            _repo.project.pms.capitalize()
        ))()

        _destination = os.path.join(
            settings.MIGASFREE_PUBLIC_DIR,
            _repo.project.slug,
            _pms.relative_path,
            _slug
        )
        shutil.rmtree(_destination, ignore_errors=True)

    #@shared_task(queue = 'repository')
    @staticmethod
    def create_repository_metadata(repo_id):
        _repo = Repository.objects.get(id=repo_id)

        exec('from migasfree.core.pms import %s' % _repo.project.pms)
        _pms = eval('%s.%s' % (
            _repo.project.pms,
            _repo.project.pms.capitalize()
        ))()


        _tmp_path = os.path.join(
            settings.MIGASFREE_PUBLIC_DIR,
            _repo.project.slug,
            'tmp'
        )
        _stores_path = os.path.join(
            settings.MIGASFREE_PUBLIC_DIR,
            _repo.project.slug,
            'stores'
        )
        _slug_tmp_path = os.path.join(
            settings.MIGASFREE_PUBLIC_DIR,
            _repo.project.slug,
            'tmp',
            _pms.relative_path
        )

        if _slug_tmp_path.endswith('/'):
            # remove trailing slash for replacing in template
            _slug_tmp_path = _slug_tmp_path[:-1]

        _pkg_tmp_path = os.path.join(
            _slug_tmp_path,
            _repo.slug,
            'PKGS'
        )
        if not os.path.exists(_pkg_tmp_path):
            os.makedirs(_pkg_tmp_path)

        for _pkg_id in _repo.available_packages.values_list('id', flat=True):
            _pkg = Package.objects.get(id=_pkg_id)
            _dst = os.path.join(_slug_tmp_path, _repo.slug, 'PKGS', _pkg.name)
            if not os.path.lexists(_dst):
                os.symlink(
                    os.path.join(_stores_path, _pkg.store.slug, _pkg.name),
                    _dst
                )

        _ret, _output, _error = _pms.create_repository(
            _repo.slug, _slug_tmp_path
        )

        _source = os.path.join(
            _tmp_path,
            _pms.relative_path,
            _repo.slug
        )
        _target = os.path.join(
            settings.MIGASFREE_PUBLIC_DIR,
            _repo.project.slug,
            _pms.relative_path,
            _repo.slug
        )
        shutil.rmtree(_target, ignore_errors=True)
        shutil.copytree(_source, _target, symlinks=True)
        shutil.rmtree(_tmp_path)

        return (_ret, _output if _ret == 0 else _error)

    @staticmethod
    def available_repos(project_id, attributes):
        """
        Return available repositories for a project and attributes list
        """
        # 1.- all repositories by attribute
        attributed = Repository.objects.filter(project__id=project_id).filter(
            enabled=True
        ).filter(
            included_attributes__id__in=attributes
        ).values_list('id', flat=True)
        lst = list(attributed)

        # 2.- all repositories by schedule
        scheduled = Repository.objects.filter(project__id=project_id).filter(
            enabled=True
        ).filter(schedule__scheduledelay__attributes__id__in=attributes).extra(
            select={'delay': "core_scheduledelay.delay"}
        )

        for repo in scheduled:
            if time_horizon(repo.start_date, repo.delay) <= datetime.now().date():
                lst.append(repo.id)

        # 3.- excluded attributtes
        repos = Repository.objects.filter(id__in=lst).filter(
            ~Q(excluded_attributes__id__in=attributes)
        )

        return repos

    class Meta:
        app_label = 'core'
        verbose_name = _('Repository')
        verbose_name_plural = _('Repositories')
        unique_together = (('name', 'project'),)


@receiver(pre_save, sender=Repository)
def pre_save_repository(sender, instance, **kwargs):
    if instance.id:
        old_obj = Repository.objects.get(pk=instance.id)
        if old_obj.project.id != instance.project.id:
            raise ValidationError(_('Is not allowed change project'))


@receiver(pre_delete, sender=Repository)
def pre_delete_repository(sender, instance, **kwargs):
    exec('from migasfree.core.pms import %s' % instance.project.pms)
    _pms = eval('%s.%s' % (
        instance.project.pms,
        instance.project.pms.capitalize()
    ))()

    _path = os.path.join(
        settings.MIGASFREE_PUBLIC_DIR,
        instance.project.slug,
        _pms.relative_path,
        instance.slug
    )
    if os.path.exists(_path):
        shutil.rmtree(_path)
