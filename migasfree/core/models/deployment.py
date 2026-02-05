# Copyright (c) 2015-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2026 Alberto Gacías <alberto@migasfree.org>
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

import datetime
import logging
import os
import shutil

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Mod
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_redis import get_redis_connection

from ...utils import is_safe_url, normalize_line_breaks, time_horizon
from ..pms import get_pms
from .attribute import Attribute
from .domain import Domain
from .migas_link import MigasLink
from .package import Package
from .package_set import PackageSet
from .project import Project
from .schedule import Schedule

logger = logging.getLogger('migasfree')


class DeploymentQuerySet(models.QuerySet):
    def scope(self, user):
        if user and not user.is_view_all():
            qs = self.filter(project__in=user.get_projects())
            domain = user.domain_preference
            if domain:
                qs = qs.filter(Q(domain_id=domain.id) | Q(domain_id=None))
            return qs

        return self

    def available(self, computer, attributes):
        """
        Consolidates common filtering logic for available deployments.
        """
        return (
            self.filter(project_id=computer.project_id, enabled=True)
            .filter(
                Q(domain__isnull=True)
                | (
                    Q(domain__included_attributes__id__in=attributes)
                    & ~Q(domain__excluded_attributes__id__in=attributes)
                )
            )
            .filter(~Q(excluded_attributes__id__in=attributes))
        )


class DeploymentManager(models.Manager):
    def get_queryset(self):
        return DeploymentQuerySet(self.model, using=self._db).select_related('project', 'schedule', 'domain')

    def scope(self, user):
        return self.get_queryset().scope(user)

    def available_deployments(self, computer, attributes):
        """
        Return available deployments for a computer and attributes list
        """
        now = timezone.localtime(timezone.now()).date()
        # Initial filtered queryset
        qs = self.get_queryset().available(computer, attributes)

        # 1. Directly available by included attributes
        attributed_ids = list(
            qs.filter(included_attributes__id__in=attributes, start_date__lte=now).values_list('id', flat=True)
        )

        # 2. Available by schedule
        # Instead of looping, we use the monotonic property of time_horizon.
        # time_horizon(start_date, delay + duration) <= now
        # means delay + duration <= max_delta_allowed (where time_horizon(start_date, max_delta) <= now)
        # However, since computer.id % duration is involved, we still need some logic.
        # But we can at least filter by schedule attributes first.
        scheduled = qs.filter(schedule__delays__attributes__id__in=attributes).annotate(
            delay=F('schedule__delays__delay'), duration=F('schedule__delays__duration')
        )

        lst = attributed_ids
        for deploy in scheduled:
            # Since this is for a specific computer, there's no need to loop over duration.
            # We just check the specific duration offset for this computer.
            val = computer.id % deploy.duration
            if time_horizon(deploy.start_date, deploy.delay + val) <= now:
                lst.append(deploy.id)

        return self.get_queryset().filter(id__in=lst).order_by('name')


class Deployment(models.Model, MigasLink):
    SOURCE_INTERNAL = 'I'
    SOURCE_EXTERNAL = 'E'

    SOURCE_CHOICES = (
        (SOURCE_INTERNAL, _('Internal')),
        (SOURCE_EXTERNAL, _('External')),
    )

    enabled = models.BooleanField(
        verbose_name=_('enabled'),
        default=True,
        help_text=_('if you uncheck this field, deployment is disabled for all computers.'),
        db_comment='indicates whether deployment is enabled',
    )

    name = models.CharField(
        max_length=50,
        verbose_name=_('name'),
        db_comment='deployment name',
    )

    slug = models.SlugField(
        max_length=50,
        verbose_name=_('slug'),
        db_comment='slug name',
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_('project'),
        db_comment='related project',
    )

    domain = models.ForeignKey(
        Domain,
        verbose_name=_('domain'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_comment='related domain',
    )

    comment = models.TextField(
        verbose_name=_('comment'),
        null=True,
        blank=True,
        db_comment='deployment comments',
    )

    packages_to_install = models.TextField(
        verbose_name=_('packages to install'),
        null=True,
        blank=True,
        help_text=_('Mandatory packages to install each time'),
        db_comment='lists the packages that will be automatically installed'
        " when a computer's attributes match the deployment",
    )

    packages_to_remove = models.TextField(
        verbose_name=_('packages to remove'),
        null=True,
        blank=True,
        help_text=_('Mandatory packages to remove each time'),
        db_comment='lists the packages that will be automatically removed when'
        " a computer's attributes match the deployment",
    )

    included_attributes = models.ManyToManyField(
        Attribute,
        related_name='deployment_included',
        blank=True,
        verbose_name=_('included attributes'),
    )

    excluded_attributes = models.ManyToManyField(
        Attribute,
        related_name='deployment_excluded',
        blank=True,
        verbose_name=_('excluded attributes'),
    )

    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        verbose_name=_('schedule'),
        null=True,
        blank=True,
        db_comment='related schedule',
    )

    start_date = models.DateField(
        default=timezone.localdate,
        verbose_name=_('start date'),
        db_comment='initial date from which the deployment will be accessible',
    )

    auto_restart = models.BooleanField(
        verbose_name=_('auto restart'),
        default=False,
        db_comment='indicates that start date is updated once the deployment is complete,'
        ' ensuring an automatic restart of the process',
    )

    default_preincluded_packages = models.TextField(
        verbose_name=_('default pre-included packages'),
        null=True,
        blank=True,
        db_comment='can be used to install packages that configure repositories external to migasfree',
    )

    default_included_packages = models.TextField(
        verbose_name=_('default included packages'),
        null=True,
        blank=True,
        db_comment='packages to be installed when tags are set on the computer',
    )

    default_excluded_packages = models.TextField(
        verbose_name=_('default excluded packages'),
        null=True,
        blank=True,
        db_comment='packages to be uninstalled when tags are set on the computer',
    )

    source = models.CharField(
        verbose_name=_('source'),
        max_length=1,
        null=False,
        choices=SOURCE_CHOICES,
        default=SOURCE_INTERNAL,
        db_comment='indicates if the deployment originates from an internal (I) or external (E) source',
    )

    available_packages = models.ManyToManyField(
        Package,
        blank=True,
        verbose_name=_('available packages'),
        help_text=_('If a computer has installed one of these packages it will be updated'),
    )

    available_package_sets = models.ManyToManyField(
        PackageSet,
        blank=True,
        verbose_name=_('available package sets'),
        help_text=_('If a computer has installed one of these packages it will be updated'),
    )

    base_url = models.CharField(
        max_length=100,
        verbose_name=_('base url'),
        null=True,
        blank=True,
        db_comment='external source base url',
    )

    # https://manpages.debian.org/stretch/apt/sources.list.5.en.html
    # https://linux.die.net/man/5/yum.conf
    options = models.CharField(
        max_length=250,
        verbose_name=_('options'),
        null=True,
        blank=True,
        db_comment='allows you to specify the different options that we need for the external repository',
    )

    suite = models.CharField(
        max_length=50,
        verbose_name=_('suite'),
        null=True,
        blank=True,
        db_comment='usually indicates the specific name of the distro (external source)',
    )

    components = models.CharField(
        max_length=100,
        verbose_name=_('components'),
        null=True,
        blank=True,
        db_comment='the various components of the source are listed (external)',
    )

    frozen = models.BooleanField(
        verbose_name=_('frozen'),
        default=True,
        db_comment='indicates whether the public repository metadata is updated or not',
    )

    expire = models.IntegerField(
        verbose_name=_('metadata cache minutes. Default 1440 minutes = 1 day'),
        default=1440,  # 60m * 24h = 1 day
        db_comment="minutes that the public repository's metadata will remain cached"
        ' (only taken into account in the case where the frozen is false)',
    )

    objects = DeploymentManager()

    def __str__(self):
        return str(self.name)

    @staticmethod
    def get_percent(begin_date, end_date):
        delta = end_date - begin_date
        aware_date = timezone.make_aware(
            datetime.datetime.combine(begin_date, datetime.datetime.min.time()), timezone.get_default_timezone()
        )
        progress = timezone.localtime(timezone.now()) - aware_date

        if delta.days > 0:
            percent = float(progress.days) / delta.days * 100
            if percent > 100:
                percent = 100
            elif percent < 0:
                percent = 0
        else:
            percent = 100

        return int(percent)

    def schedule_timeline(self):
        if self.schedule is None:
            return None

        # Use related manager to benefit from prefetch_related if available
        delays = list(self.schedule.delays.order_by('delay'))

        if not delays:
            return None

        begin_date = time_horizon(self.start_date, delays[0].delay)
        end_date = time_horizon(self.start_date, delays[-1].delay + delays[-1].duration)

        return {
            'begin_date': str(begin_date),
            'end_date': str(end_date),
            'percent': self.get_percent(begin_date, end_date),
        }

    def timeline(self):
        schedule_timeline = self.schedule_timeline()

        if not schedule_timeline:
            return None

        date_format = '%Y-%m-%d'
        begin_date = datetime.datetime.strptime(schedule_timeline['begin_date'], date_format)
        end_date = datetime.datetime.strptime(schedule_timeline['end_date'], date_format)

        days = (datetime.datetime.today() - begin_date).days + 1
        total_days = (end_date - begin_date).days
        return {
            'deployment_id': self.pk,
            'percent': schedule_timeline['percent'],
            'schedule': self.schedule,
            'info': _('%s/%s days (from %s to %s)')
            % (days, total_days, schedule_timeline['begin_date'], schedule_timeline['end_date']),
        }

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.slug = slugify(self.name)

        properties_to_normalize = [
            'packages_to_install',
            'packages_to_remove',
            'default_preincluded_packages',
            'default_included_packages',
            'default_excluded_packages',
        ]

        for property_name in properties_to_normalize:
            setattr(self, property_name, normalize_line_breaks(getattr(self, property_name)))

        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

        try:
            from ...stats import tasks

            tasks.assigned_computers_to_deployment(self.id)
        except Exception as e:
            logger.warning('Failed to run assigned_computers_to_deployment task: %s', e)

    @staticmethod
    def available_deployments(computer, attributes):
        """
        Return available deployments for a computer and attributes list
        """
        return Deployment.objects.available_deployments(computer, attributes)

    def clear_cache(self):
        con = get_redis_connection()
        con.delete(f'migasfree:deployments:{self.id}:computers')

    def related_objects(self, model, user):
        """
        Returns Queryset with the related computers based in attributes and schedule
        """
        if model != 'computer' or not self.enabled or self.start_date > timezone.localtime(timezone.now()).date():
            return None

        from ...client.models import Computer

        # 1. Base computers by project and scope
        computers = Computer.productive.scope(user).filter(project_id=self.project_id)

        # 2. Build filter for attributes and schedule
        # Initial filter: specifically included attributes
        q_filter = Q(sync_attributes__id__in=self.included_attributes.values_list('id', flat=True))

        # Add schedule filters
        if self.schedule:
            now = timezone.localtime(timezone.now()).date()
            for delay in self.schedule.delays.all():
                delay_attributes = list(delay.attributes.values_list('id', flat=True))
                # Monotonic optimization: find max duration k such that time_horizon(start+delay+k) <= now
                max_k = -1
                for k in range(delay.duration):
                    if time_horizon(self.start_date, delay.delay + k) <= now:
                        max_k = k
                    else:
                        break

                if max_k != -1:
                    if max_k == delay.duration - 1:
                        # All computers with these attributes are allowed
                        q_filter |= Q(sync_attributes__id__in=delay_attributes)
                    else:
                        # Only computers with id % duration <= max_k
                        # We use annotate here, but since we have multiple delays, we name them uniquely
                        computers = computers.annotate(**{f'mod_{delay.id}': Mod('id', delay.duration)})
                        q_filter |= Q(sync_attributes__id__in=delay_attributes, **{f'mod_{delay.id}__lte': max_k})

        # Apply positive filters and negative (excluded attributes)
        return (
            computers.filter(q_filter)
            .exclude(sync_attributes__id__in=self.excluded_attributes.values_list('id', flat=True))
            .distinct()
        )

    def pms(self):
        return get_pms(self.project.pms)

    def path(self, name=None):
        return os.path.join(
            Project.path(self.project.slug),
            self.pms().relative_path
            if self.source == Deployment.SOURCE_INTERNAL
            else settings.MIGASFREE_EXTERNAL_TRAILING_PATH,
            name if name else self.slug,
        )

    def source_template(self):
        return self.pms().source_template(self)

    def can_delete(self, user):
        return user.has_perm('core.delete_deployment') and (
            not user.userprofile.domains.count() or self.domain == user.userprofile.domain_preference
        )

    def get_repository_metadata_payload(self):
        """
        Returns a dictionary with all the data needed by the create_repository_metadata task,
        avoiding API calls from the worker.
        """
        # Collect all packages (direct + package sets)
        packages = list(self.available_packages.select_related('store').all())

        for package_set in self.available_package_sets.prefetch_related('packages__store'):
            packages.extend(list(package_set.packages.all()))

        # Serialize packages
        packages_data = []
        for pkg in packages:
            if pkg.store:  # Only include packages with a store
                packages_data.append(
                    {
                        'id': pkg.id,
                        'fullname': pkg.fullname,
                        'store': {'name': pkg.store.name},
                    }
                )

        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'project': {
                'name': self.project.name,
                'slug': self.project.slug,
                'pms': self.project.pms,
                'architecture': self.project.architecture,
            },
            'available_packages': packages_data,
        }

    class Meta:
        app_label = 'core'
        verbose_name = _('Deployment')
        verbose_name_plural = _('Deployments')
        unique_together = (('name', 'project'), ('project', 'slug'))
        ordering = ['project__name', 'name']
        db_table_comment = 'repositories of packages and associated actions to be executed on computers'
        ' that meet the required attributes'


@receiver(pre_save, sender=Deployment)
def pre_save_deployment(sender, instance, **kwargs):
    if instance.id:
        # Use .values() to limit database load when checking old state
        old_data = (
            Deployment.objects.filter(pk=instance.id)
            .values('project_id', 'packages_to_install', 'packages_to_remove')
            .first()
        )

        if not old_data:
            return

        if old_data['project_id'] != instance.project_id:
            raise ValidationError(_('Is not allowed change project'))

        if (
            # NOTE: available_packages comparison is complex due to M2M,
            # usually M2M changes don't trigger pre_save unless the model itself is saved.
            # But the logic here was checking for field changes.
            instance.packages_to_install != old_data['packages_to_install']
            or instance.packages_to_remove != old_data['packages_to_remove']
        ):
            instance.clear_cache()


@receiver(pre_delete, sender=Deployment)
def pre_delete_deployment(sender, instance, **kwargs):
    path = instance.path()
    if os.path.exists(path):
        shutil.rmtree(path)

    instance.clear_cache()


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

    def clean(self):
        super().clean()
        if self.base_url and not is_safe_url(self.base_url):
            raise ValidationError({'base_url': _('Invalid or unsafe URL')})

    class Meta:
        app_label = 'core'
        verbose_name = _('Deployment (external source)')
        verbose_name_plural = _('Deployments (external source)')
        proxy = True
