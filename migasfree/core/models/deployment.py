# -*- coding: utf-8 -*-

# Copyright (c) 2015-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2021 Alberto Gacías <alberto@migasfree.org>
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

from importlib import import_module

from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_redis import get_redis_connection

from ...utils import time_horizon

from .migas_link import MigasLink
from .project import Project
from .package import Package
from .package_set import PackageSet
from .attribute import Attribute
from .schedule import Schedule
from .schedule_delay import ScheduleDelay
from .domain import Domain


class DeploymentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'project', 'schedule', 'domain'
        )

    def scope(self, user):
        qs = self.get_queryset()
        if not user.is_view_all():
            qs = qs.filter(project__in=user.get_projects())
            domain = user.domain_preference
            if domain:
                qs = qs.filter(Q(domain_id=domain.id) | Q(domain_id=None))

        return qs


class Deployment(models.Model, MigasLink):
    SOURCE_INTERNAL = 'I'
    SOURCE_EXTERNAL = 'E'

    SOURCE_CHOICES = (
        (SOURCE_INTERNAL, _('Internal')),
        (SOURCE_EXTERNAL, _('External')),
    )

    PACKAGES_PATH = 'PKGS'

    enabled = models.BooleanField(
        verbose_name=_('enabled'),
        default=True,
        help_text=_('if you uncheck this field, deployment is disabled for all computers.')
    )

    name = models.CharField(
        max_length=50,
        verbose_name=_('name')
    )

    slug = models.SlugField(
        max_length=50,
        verbose_name=_('slug')
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_('project')
    )

    domain = models.ForeignKey(
        Domain,
        verbose_name=_('domain'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    comment = models.TextField(
        verbose_name=_('comment'),
        null=True,
        blank=True
    )

    packages_to_install = models.TextField(
        verbose_name=_('packages to install'),
        null=True,
        blank=True,
        help_text=_('Mandatory packages to install each time')
    )

    packages_to_remove = models.TextField(
        verbose_name=_('packages to remove'),
        null=True,
        blank=True,
        help_text=_('Mandatory packages to remove each time')
    )

    included_attributes = models.ManyToManyField(
        Attribute,
        related_name='deployment_included',
        blank=True,
        verbose_name=_('included attributes')
    )

    excluded_attributes = models.ManyToManyField(
        Attribute,
        related_name='deployment_excluded',
        blank=True,
        verbose_name=_('excluded attributes')
    )

    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        verbose_name=_('schedule'),
        null=True,
        blank=True
    )

    start_date = models.DateField(
        default=timezone.now,
        verbose_name=_('start date')
    )

    default_preincluded_packages = models.TextField(
        verbose_name=_('default pre-included packages'),
        null=True,
        blank=True
    )

    default_included_packages = models.TextField(
        verbose_name=_('default included packages'),
        null=True,
        blank=True
    )

    default_excluded_packages = models.TextField(
        verbose_name=_('default excluded packages'),
        null=True,
        blank=True
    )

    source = models.CharField(
        verbose_name=_('source'),
        max_length=1,
        null=False,
        choices=SOURCE_CHOICES,
        default=SOURCE_INTERNAL
    )

    available_packages = models.ManyToManyField(
        Package,
        blank=True,
        verbose_name=_('available packages'),
        help_text=_('If a computer has installed one of these packages it will be updated')
    )

    available_package_sets = models.ManyToManyField(
        PackageSet,
        blank=True,
        verbose_name=_('available package sets'),
        help_text=_('If a computer has installed one of these packages it will be updated')
    )

    base_url = models.CharField(
        max_length=100,
        verbose_name=_('base url'),
        null=True,
        blank=True
    )

    # https://manpages.debian.org/stretch/apt/sources.list.5.en.html
    # https://linux.die.net/man/5/yum.conf
    options = models.CharField(
        max_length=250,
        verbose_name=_('options'),
        null=True,
        blank=True
    )

    suite = models.CharField(
        max_length=50,
        verbose_name=_('suite'),
        null=True,
        blank=True
    )

    components = models.CharField(
        max_length=100,
        verbose_name=_('components'),
        null=True,
        blank=True
    )

    frozen = models.BooleanField(
        verbose_name=_('frozen'),
        default=True
    )

    expire = models.IntegerField(
        verbose_name=_('metadata cache minutes. Default 1440 minutes = 1 day'),
        default=1440  # 60m * 24h = 1 day
    )

    objects = DeploymentManager()

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

        return int(percent)

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
            'percent': self.get_percent(begin_date, end_date)
        }

    def timeline(self):
        schedule_timeline = self.schedule_timeline()

        if not schedule_timeline:
            return None

        date_format = "%Y-%m-%d"
        begin_date = datetime.datetime.strptime(
            schedule_timeline['begin_date'],
            date_format
        )
        end_date = datetime.datetime.strptime(
            schedule_timeline['end_date'],
            date_format
        )

        days = (datetime.datetime.today() - begin_date).days + 1
        total_days = (end_date - begin_date).days
        return {
            'deployment_id': self.pk,
            'percent': schedule_timeline['percent'],
            'schedule': self.schedule,
            'info': _('%s/%s days (from %s to %s)') % (
                days,
                total_days,
                schedule_timeline['begin_date'],
                schedule_timeline['end_date']
            )
        }

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.slug = slugify(self.name)

        if self.packages_to_install:
            self.packages_to_install = self.packages_to_install.replace("\r\n", "\n")
        if self.packages_to_remove:
            self.packages_to_remove = self.packages_to_remove.replace("\r\n", "\n")

        if self.default_preincluded_packages:
            self.default_preincluded_packages = self.default_preincluded_packages.replace("\r\n", "\n")
        if self.default_included_packages:
            self.default_included_packages = self.default_included_packages.replace("\r\n", "\n")
        if self.default_excluded_packages:
            self.default_excluded_packages = self.default_excluded_packages.replace("\r\n", "\n")

        super().save(force_insert, force_update, using, update_fields)

        try:
            from ...stats import tasks
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
            project__id=computer.project.id,
            enabled=True,
            included_attributes__id__in=attributes,
            start_date__lte=datetime.datetime.now().date()
        ).filter(
            Q(domain__isnull=True) | (
                Q(domain__included_attributes__id__in=attributes) &
                ~Q(domain__excluded_attributes__id__in=attributes)
            )
        ).values_list('id', flat=True)
        lst = list(attributed)

        # 2.- all deployments by schedule
        scheduled = Deployment.objects.filter(
            project__id=computer.project.id,
            enabled=True,
            schedule__delays__attributes__id__in=attributes
        ).filter(
            Q(domain__isnull=True) | (
                Q(domain__included_attributes__id__in=attributes) &
                ~Q(domain__excluded_attributes__id__in=attributes)
            )
        ).extra(
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

    def related_objects(self, model, user):
        """
        Returns Queryset with the related computers based in attributes and schedule
        """
        if model == 'computer':
            from ...client.models import Computer

            if self.enabled and (self.start_date <= datetime.datetime.now().date()):
                # by assigned attributes
                computers = Computer.productive.scope(user).filter(
                    project_id=self.project.id
                ).filter(
                    Q(sync_attributes__in=self.included_attributes.all())
                )

                # by schedule
                if self.schedule:
                    for delay in self.schedule.delays.all():
                        delay_attributes = list(delay.attributes.values_list('id', flat=True))
                        for duration in range(0, delay.duration):
                            if time_horizon(
                                self.start_date, delay.delay + duration
                            ) <= datetime.datetime.now().date():
                                computers_schedule = Computer.productive.scope(user).filter(
                                    project_id=self.project.id
                                ).filter(
                                    Q(sync_attributes__id__in=delay_attributes)
                                ).extra(
                                    where=['MOD(client_computer.id, {}) = {}'.format(delay.duration, duration)]
                                )
                                computers = (computers | computers_schedule)
                            else:
                                break

                # excluded attributes
                computers = computers.exclude(
                    Q(sync_attributes__in=self.excluded_attributes.all())
                )

                return computers.distinct()

        return None

    def pms(self):
        mod = import_module('migasfree.core.pms.{}'.format(self.project.pms))
        return getattr(mod, self.project.pms.capitalize())()

    def path(self, name=None):
        return os.path.join(
            Project.path(self.project.slug),
            self.pms().relative_path,
            name if name else self.slug
        )

    def source_template(self):
        return self.pms().source_template(self)

    def can_delete(self, user):
        if user.has_perm("core.delete_deployment"):
            if user.userprofile.domains.count() == 0 or self.domain == user.userprofile.domain_preference:
                return True

        return False

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
            con = get_redis_connection()
            con.delete('migasfree:deployments:%d:computers' % instance.id)


@receiver(pre_delete, sender=Deployment)
def pre_delete_deployment(sender, instance, **kwargs):
    path = instance.path()
    if os.path.exists(path):
        shutil.rmtree(path)

    con = get_redis_connection()
    con.delete('migasfree:deployments:%d:computers' % instance.id)


class InternalSourceManager(DeploymentManager):
    def scope(self, user):
        return super().scope(user).filter(source=Deployment.SOURCE_INTERNAL)


class InternalSource(Deployment):
    objects = InternalSourceManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source = Deployment.SOURCE_INTERNAL

    class Meta:
        app_label = 'core'
        verbose_name = _('Deployment (internal source)')
        verbose_name_plural = _('Deployments (internal source)')
        proxy = True


class ExternalSourceManager(DeploymentManager):
    def scope(self, user):
        return super().scope(user).filter(source=Deployment.SOURCE_EXTERNAL)


class ExternalSource(Deployment):
    objects = ExternalSourceManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source = Deployment.SOURCE_EXTERNAL

    class Meta:
        app_label = 'core'
        verbose_name = _('Deployment (external source)')
        verbose_name_plural = _('Deployments (external source)')
        proxy = True
