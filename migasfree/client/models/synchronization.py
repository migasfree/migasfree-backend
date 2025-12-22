# Copyright (c) 2015-2024 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2024 Alberto Gacías <alberto@migasfree.org>
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

from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django_redis import get_redis_connection

from ...core.models import Deployment, Project
from .event import Event
from .user import User


class DomainSynchronizationManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                'computer',
                'computer__project',
                'computer__sync_user',
                'project',
                'user',
            )
        )

    def scope(self, user):
        qs = self.get_queryset()
        if user and not user.is_view_all():
            qs = qs.filter(computer_id__in=user.get_computers())

        return qs


class SynchronizationManager(DomainSynchronizationManager):
    def create(self, computer, consumer=None, start_date=None, pms_status_ok=False):
        obj = Synchronization()
        obj.computer = computer
        obj.project = computer.project
        obj.user = computer.sync_user
        obj.consumer = consumer
        obj.start_date = start_date
        obj.pms_status_ok = pms_status_ok
        obj.save()

        # Associate errors and faults created from start_date onwards
        # Import here to avoid circular dependency
        from .error import Error
        from .fault import Fault

        if start_date:
            # Associate errors/faults created from start_date onwards
            Error.objects.filter(computer=computer, synchronization__isnull=True, created_at__gte=start_date).update(
                synchronization=obj
            )

            Fault.objects.filter(computer=computer, synchronization__isnull=True, created_at__gte=start_date).update(
                synchronization=obj
            )

        return obj


class Synchronization(Event):
    start_date = models.DateTimeField(
        verbose_name=_('start date connection'),
        null=True,
        blank=True,
        db_comment='start date connection',
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('user'),
        db_comment='user logged into the graphical session at the time of computer sync',
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_('project'),
        null=True,
        db_comment='project to which the computer belongs',
    )

    consumer = models.CharField(
        verbose_name=_('consumer'),
        max_length=50,
        null=True,
        db_comment='application that has done the synchronization',
    )

    pms_status_ok = models.BooleanField(
        verbose_name=_('PMS status OK'),
        default=False,
        help_text=_('indicates the status of transactions with PMS'),
        db_comment='indicates whether the packaging system completed successfully (true for no error, false for error)',
    )

    objects = SynchronizationManager()

    @staticmethod
    def group_by_project(user):
        return (
            Synchronization.objects.scope(user)
            .values('project__id', 'project__name')
            .annotate(count=models.Count('project__id'))
            .order_by('-count')
        )

    def add_to_redis(self):
        con = get_redis_connection()

        if not con.sismember(f'migasfree:watch:stats:years:{self.created_at.year:04}', self.computer.id):
            con.incr(f'migasfree:stats:years:{self.created_at.year:04}')
            con.sadd(f'migasfree:watch:stats:years:{self.created_at.year:04}', self.computer.id)
            con.incr(f'migasfree:stats:{self.project.id}:years:{self.created_at.year:04}')
            con.sadd(f'migasfree:watch:stats:{self.project.id}:years:{self.created_at.year:04}', self.computer.id)

        if not con.sismember(
            f'migasfree:watch:stats:months:{self.created_at.year:04}{self.created_at.month:02}', self.computer.id
        ):
            con.incr(f'migasfree:stats:months:{self.created_at.year:04}{self.created_at.month:02}')
            con.sadd(
                f'migasfree:watch:stats:months:{self.created_at.year:04}{self.created_at.month:02}',
                self.computer.id,
            )
            con.incr(f'migasfree:stats:{self.project.id}:months:{self.created_at.year:04}{self.created_at.month:02}')
            con.sadd(
                f'migasfree:watch:stats:{self.project.id}:months:{self.created_at.year:04}{self.created_at.month:02}',
                self.computer.id,
            )

        if not con.sismember(
            f'migasfree:watch:stats:days:{self.created_at.year:04}{self.created_at.month:02}{self.created_at.day:02}',
            self.computer.id,
        ):
            con.incr(
                f'migasfree:stats:days:{self.created_at.year:04}{self.created_at.month:02}{self.created_at.day:02}'
            )
            con.sadd(
                f'migasfree:watch:stats:days:{self.created_at.year:04}{self.created_at.month:02}{self.created_at.day:02}',
                self.computer.id,
            )
            con.incr(
                f'migasfree:stats:{self.project.id}:days:'
                f'{self.created_at.year:04}{self.created_at.month:02}{self.created_at.day:02}'
            )
            con.sadd(
                f'migasfree:watch:stats:{self.project.id}:days:'
                f'{self.created_at.year:04}{self.created_at.month:02}{self.created_at.day:02}',
                self.computer.id,
            )

        if not con.sismember(
            f'migasfree:watch:stats:hours:'
            f'{self.created_at.year:04}{self.created_at.month:02}{self.created_at.day:02}{self.created_at.hour:02}',
            self.computer.id,
        ):
            con.incr(
                f'migasfree:stats:hours:'
                f'{self.created_at.year:04}{self.created_at.month:02}{self.created_at.day:02}{self.created_at.hour:02}'
            )
            con.sadd(
                f'migasfree:watch:stats:hours:'
                f'{self.created_at.year:04}{self.created_at.month:02}{self.created_at.day:02}{self.created_at.hour:02}',
                self.computer.id,
            )
            con.incr(
                f'migasfree:stats:{self.project.id}:hours:'
                f'{self.created_at.year:04}{self.created_at.month:02}{self.created_at.day:02}{self.created_at.hour:02}'
            )
            con.sadd(
                f'migasfree:watch:stats:{self.project.id}:hours:'
                f'{self.created_at.year:04}{self.created_at.month:02}{self.created_at.day:02}{self.created_at.hour:02}',
                self.computer.id,
            )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

        deployments = Deployment.available_deployments(self.computer, self.computer.get_all_attributes()).values_list(
            'id', flat=True
        )

        con = get_redis_connection()
        for deploy_id in deployments:
            con.srem(f'migasfree:deployments:{deploy_id}:ok', self.computer.id)
            con.srem(f'migasfree:deployments:{deploy_id}:error', self.computer.id)
            con.sadd(
                f'migasfree:deployments:{deploy_id}:{"ok" if self.pms_status_ok else "error"}',
                self.computer.id,
            )

    def save_computer_sync_end_date(self):
        self.computer.sync_end_date = self.created_at
        self.computer.save(force_update=True, update_fields=['sync_end_date'])

    class Meta:
        app_label = 'client'
        verbose_name = _('Synchronization')
        verbose_name_plural = _('Synchronizations')
        indexes = [
            models.Index(fields=['created_at']),
        ]
        db_table_comment = 'synchronization processes that have occurred on computers'


@receiver(post_save, sender=Synchronization)
def post_save_sync(sender, instance, created, **kwargs):
    if created:
        instance.add_to_redis()

    if instance:
        instance.save_computer_sync_end_date()


@receiver(pre_delete, sender=Synchronization)
def pre_delete_sync(sender, instance, **kwargs):
    con = get_redis_connection()

    if con.sismember(f'migasfree:watch:stats:years:{instance.created_at.year:04}', instance.computer.id):
        con.decr(f'migasfree:stats:years:{instance.created_at.year:04}')
        con.srem(f'migasfree:watch:stats:years:{instance.created_at.year:04}', instance.computer.id)
        con.decr(f'migasfree:stats:{instance.project.id}:years:{instance.created_at.year:04}')
        con.srem(
            f'migasfree:watch:stats:{instance.project.id}:years:{instance.created_at.year:04}',
            instance.computer.id,
        )

    if con.sismember(
        f'migasfree:watch:stats:months:{instance.created_at.year:04}{instance.created_at.month:02}',
        instance.computer.id,
    ):
        con.decr(f'migasfree:stats:months:{instance.created_at.year:04}{instance.created_at.month:02}')
        con.srem(
            f'migasfree:watch:stats:months:{instance.created_at.year:04}{instance.created_at.month:02}',
            instance.computer.id,
        )
        con.decr(
            f'migasfree:stats:{instance.project.id}:months:{instance.created_at.year:04}{instance.created_at.month:02}'
        )
        con.srem(
            f'migasfree:watch:stats:{instance.project.id}:months:'
            f'{instance.created_at.year:04}{instance.created_at.month:02}',
            instance.computer.id,
        )

    if con.sismember(
        f'migasfree:watch:stats:days:'
        f'{instance.created_at.year:04}{instance.created_at.month:02}{instance.created_at.day:02}',
        instance.computer.id,
    ):
        con.decr(
            f'migasfree:stats:days:'
            f'{instance.created_at.year:04}{instance.created_at.month:02}{instance.created_at.day:02}'
        )
        con.srem(
            f'migasfree:watch:stats:days:'
            f'{instance.created_at.year:04}{instance.created_at.month:02}{instance.created_at.day:02}',
            instance.computer.id,
        )
        con.decr(
            f'migasfree:stats:{instance.project.id}:days:'
            f'{instance.created_at.year:04}{instance.created_at.month:02}{instance.created_at.day:02}'
        )
        con.srem(
            f'migasfree:watch:stats:{instance.project.id}:days:'
            f'{instance.created_at.year:04}{instance.created_at.month:02}{instance.created_at.day:02}',
            instance.computer.id,
        )

    if con.sismember(
        f'migasfree:watch:stats:hours:'
        f'{instance.created_at.year:04}{instance.created_at.month:02}'
        f'{instance.created_at.day:02}{instance.created_at.hour:02}',
        instance.computer.id,
    ):
        con.decr(
            f'migasfree:stats:hours:'
            f'{instance.created_at.year:04}{instance.created_at.month:02}'
            f'{instance.created_at.day:02}{instance.created_at.hour:02}'
        )
        con.srem(
            f'migasfree:watch:stats:hours:'
            f'{instance.created_at.year:04}{instance.created_at.month:02}'
            f'{instance.created_at.day:02}{instance.created_at.hour:02}',
            instance.computer.id,
        )
        con.decr(
            f'migasfree:stats:{instance.project.id}:hours:'
            f'{instance.created_at.year:04}{instance.created_at.month:02}'
            f'{instance.created_at.day:02}{instance.created_at.hour:02}'
        )
        con.srem(
            f'migasfree:watch:stats:{instance.project.id}:hours:'
            f'{instance.created_at.year:04}{instance.created_at.month:02}'
            f'{instance.created_at.day:02}{instance.created_at.hour:02}',
            instance.computer.id,
        )
