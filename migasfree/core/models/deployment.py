# -*- coding: utf-8 -*-

# Copyright (c) 2015-2016 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2016 Alberto Gacías <alberto@migasfree.org>
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
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django_redis import get_redis_connection

from migasfree.utils import time_horizon

from .project import Project
from .package import Package
from .attribute import Attribute
from .schedule import Schedule
from .schedule_delay import ScheduleDelay


@python_2_unicode_compatible
class Deployment(models.Model):
    enabled = models.BooleanField(
        verbose_name=_('enabled'),
        default=True,
        help_text=_("if you uncheck this field, deployment is disabled for all"
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
        blank=True,
        verbose_name=_("included")
    )

    excluded_attributes = models.ManyToManyField(
        Attribute,
        related_name="ExcludeAttribute",
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
        default=timezone.now,
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

    @staticmethod
    def get_percent(begin_date, end_date):
        delta = end_date - begin_date
        progress = datetime.datetime.now() - datetime.datetime.combine(
            begin_date, datetime.datetime.min.time()
        )

        if delta.days > 0:
            percent = float(progress.days) / delta.days * 100
            if percent > 100:
                percent = 100
        else:
            percent = 100

        return percent

    def schedule_timeline(self):
        if self.schedule is None:
            return None

        delays = ScheduleDelay.objects.filter(
            schedule__id=self.schedule.id
        ).order_by('delay')

        if len(delays) == 0:
            return None

        begin_date = time_horizon(self.start_date, delays[0].delay)
        end_date = time_horizon(
            self.start_date,
            delays.reverse()[0].delay + delays.reverse()[0].duration
        )

        return {
            'begin_date': str(begin_date),
            'end_date': str(end_date),
            'percent': '%d' % self.get_percent(begin_date, end_date)
        }

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)

        self.packages_to_install = self.packages_to_install.replace("\r\n", "\n")
        self.packages_to_remove = self.packages_to_remove.replace("\r\n", "\n")

        self.default_preincluded_packages = self.default_preincluded_packages.replace("\r\n", "\n")
        self.default_included_packages = self.default_included_packages.replace("\r\n", "\n")
        self.default_excluded_packages = self.default_excluded_packages.replace("\r\n", "\n")

        super(Deployment, self).save(*args, **kwargs)

        try:
            from migasfree.stats import tasks
            tasks.assigned_computers_to_deployment(self.id)
        except:
            pass

    @staticmethod
    def available_deployments(computer, attributes):
        """
        Return available deployments for a computer and attributes list
        """
        # 1.- all deployments by attribute
        attributed = Deployment.objects.filter(
            project__id=computer.project.id
        ).filter(
            enabled=True
        ).filter(
            included_attributes__id__in=attributes
        ).filter(
            start_date__lte=datetime.datetime.now().date()
        ).values_list('id', flat=True)
        lst = list(attributed)

        # 2.- all deployments by schedule
        scheduled = Deployment.objects.filter(
            project__id=computer.project.id
        ).filter(
            enabled=True
        ).filter(schedule__delays__attributes__id__in=attributes).extra(
            select={
                'delay': 'core_scheduledelay.delay',
                'duration': 'core_scheduledelay.duration'
            }
        )

        for deploy in scheduled:
            for duration in range(0, deploy.duration):
                if computer.id % deploy.duration == duration:
                    if time_horizon(
                        deploy.start_date, deploy.delay + duration
                    ) <= datetime.datetime.now().date():
                        lst.append(deploy.id)
                        break

        # 3.- excluded attributes
        deployments = Deployment.objects.filter(id__in=lst).filter(
            ~Q(excluded_attributes__id__in=attributes)
        ).order_by('name')

        return deployments

    def pms(self):
        mod = import_module('migasfree.core.pms.%s' % self.project.pms)
        return getattr(mod, self.project.pms.capitalize())()

    def path(self, name=None):
        return os.path.join(
            Project.path(self.project.slug),
            self.pms.relative_path,
            name if name else self.slug
        )

    class Meta:
        app_label = 'core'
        verbose_name = _('Deployment')
        verbose_name_plural = _('Deployments')
        unique_together = (('name', 'project'),)
        ordering = ['project__name', 'name']


@receiver(pre_save, sender=Deployment)
def pre_save_deployment(sender, instance, **kwargs):
    if instance.id:
        old_obj = Deployment.objects.get(pk=instance.id)
        if old_obj.project.id != instance.project.id:
            raise ValidationError(_('Is not allowed change project'))

        if instance.available_packages != old_obj.available_packages \
                or instance.packages_to_install != old_obj.packages_to_install \
                or instance.packages_to_remove != old_obj.packages_to_remove:
            con = get_redis_connection('default')
            con.delete('migasfree:deployments:%d:computers' % instance.id)


@receiver(pre_delete, sender=Deployment)
def pre_delete_deployment(sender, instance, **kwargs):
    path = instance.path()
    if os.path.exists(path):
        shutil.rmtree(path)

    con = get_redis_connection('default')
    con.delete('migasfree:deployments:%d:computers' % instance.id)
