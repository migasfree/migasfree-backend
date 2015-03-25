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

from __future__ import absolute_import

import os
import shutil
import datetime

from importlib import import_module

from django.db import models
from django.template.defaultfilters import slugify
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.db.models import Q
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django_redis import get_redis_connection
from celery import shared_task

from migasfree.utils import time_horizon

from .project import Project
from .package import Package
from .attribute import Attribute
from .schedule import Schedule


@python_2_unicode_compatible
class Release(models.Model):
    enabled = models.BooleanField(
        verbose_name=_('enabled'),
        default=True,
        help_text=_("if you uncheck this field, release is disabled for all"
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

        super(Release, self).save(*args, **kwargs)

        try:
            from migasfree.stats import tasks
            tasks.assigned_computers_to_release(self.id)
        except:
            pass

    @staticmethod
    def available_repos(project_id, attributes):
        """
        Return available repositories for a project and attributes list
        """
        # 1.- all repositories by attribute
        attributed = Release.objects.filter(project__id=project_id).filter(
            enabled=True
        ).filter(
            included_attributes__id__in=attributes
        ).values_list('id', flat=True)
        lst = list(attributed)

        # 2.- all repositories by schedule
        scheduled = Release.objects.filter(project__id=project_id).filter(
            enabled=True
        ).filter(schedule__scheduledelay__attributes__id__in=attributes).extra(
            select={'delay': "core_scheduledelay.delay"}
        )

        for repo in scheduled:
            if time_horizon(repo.start_date, repo.delay) <= datetime.now().date():
                lst.append(repo.id)

        # 3.- excluded attributtes
        repos = Release.objects.filter(id__in=lst).filter(
            ~Q(excluded_attributes__id__in=attributes)
        )

        return repos

    class Meta:
        app_label = 'core'
        verbose_name = _('Release')
        verbose_name_plural = _('Releases')
        unique_together = (('name', 'project'),)


@receiver(pre_save, sender=Release)
def pre_save_release(sender, instance, **kwargs):
    if instance.id:
        old_obj = Release.objects.get(pk=instance.id)
        if old_obj.project.id != instance.project.id:
            raise ValidationError(_('Is not allowed change project'))

        if instance.available_packages != old_obj.available_packages \
        or instance.packages_to_install != old_obj.packages_to_install \
        or instance.packages_to_remove != old_obj.packages_to_remove:
            con = get_redis_connection('default')
            con.delete('migasfree:releases:%d:computers' % instance.id)


@receiver(pre_delete, sender=Release)
def pre_delete_release(sender, instance, **kwargs):
    mod = import_module('migasfree.core.pms.%s' % instance.project.pms)
    pms = getattr(mod, instance.project.pms.capitalize())()

    path = os.path.join(
        settings.MIGASFREE_PUBLIC_DIR,
        instance.project.slug,
        pms.relative_path,
        instance.slug
    )
    if os.path.exists(path):
        shutil.rmtree(path)

    con = get_redis_connection('default')
    con.delete('migasfree:releases:%d:computers' % instance.id)
