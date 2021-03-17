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

from django.db import models
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django_redis import get_redis_connection

from ...core.models import Project, Deployment
from .event import Event
from .user import User


class DomainSynchronizationManager(models.Manager):
    def scope(self, user):
        qs = super().get_queryset()
        if not user.is_view_all():
            qs = qs.filter(
                computer_id__in=user.get_computers()
            )

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

        return obj


class Synchronization(Event):
    start_date = models.DateTimeField(
        verbose_name=_('start date connection'),
        null=True,
        blank=True
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("user")
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_("project"),
        null=True
    )

    consumer = models.CharField(
        verbose_name=_('consumer'),
        max_length=50,
        null=True
    )

    pms_status_ok = models.BooleanField(
        verbose_name=_('PMS status OK'),
        default=False,
        help_text=_('indicates the status of transactions with PMS')
    )

    objects = SynchronizationManager()

    @staticmethod
    def group_by_project(user):
        return Synchronization.objects.scope(user).values(
            'project__id', 'project__name'
        ).annotate(
            count=models.Count('project__id')
        ).order_by('-count')

    def add_to_redis(self):
        con = get_redis_connection()

        if not con.sismember(
            'migasfree:watch:stats:years:%04d' % self.created_at.year,
            self.computer.id
        ):
            con.incr('migasfree:stats:years:%04d' % self.created_at.year)
            con.sadd(
                'migasfree:watch:stats:years:%04d' % self.created_at.year,
                self.computer.id
            )
            con.incr('migasfree:stats:%d:years:%04d' % (
                self.project.id, self.created_at.year
            ))
            con.sadd(
                'migasfree:watch:stats:%d:years:%04d' % (
                    self.project.id, self.created_at.year
                ),
                self.computer.id
            )

        if not con.sismember(
            'migasfree:watch:stats:months:%04d%02d' % (
                self.created_at.year, self.created_at.month
            ),
            self.computer.id
        ):
            con.incr('migasfree:stats:months:%04d%02d' % (
                self.created_at.year, self.created_at.month
            ))
            con.sadd(
                'migasfree:watch:stats:months:%04d%02d' % (
                    self.created_at.year, self.created_at.month
                ),
                self.computer.id
            )
            con.incr('migasfree:stats:%d:months:%04d%02d' % (
                self.project.id, self.created_at.year, self.created_at.month
            ))
            con.sadd(
                'migasfree:watch:stats:%d:months:%04d%02d' % (
                    self.project.id, self.created_at.year, self.created_at.month
                ),
                self.computer.id
            )

        if not con.sismember(
            'migasfree:watch:stats:days:%04d%02d%02d' % (
                self.created_at.year, self.created_at.month, self.created_at.day
            ),
            self.computer.id
        ):
            con.incr('migasfree:stats:days:%04d%02d%02d' % (
                self.created_at.year, self.created_at.month, self.created_at.day
            ))
            con.sadd(
                'migasfree:watch:stats:days:%04d%02d%02d' % (
                    self.created_at.year, self.created_at.month, self.created_at.day
                ),
                self.computer.id
            )
            con.incr('migasfree:stats:%d:days:%04d%02d%02d' % (
                self.project.id, self.created_at.year,
                self.created_at.month, self.created_at.day
            ))
            con.sadd(
                'migasfree:watch:stats:%d:days:%04d%02d%02d' % (
                    self.project.id, self.created_at.year,
                    self.created_at.month, self.created_at.day
                ),
                self.computer.id
            )

        if not con.sismember(
            'migasfree:watch:stats:hours:%04d%02d%02d%02d' % (
                self.created_at.year, self.created_at.month,
                self.created_at.day, self.created_at.hour
            ),
            self.computer.id
        ):
            con.incr('migasfree:stats:hours:%04d%02d%02d%02d' % (
                self.created_at.year, self.created_at.month,
                self.created_at.day, self.created_at.hour
            ))
            con.sadd(
                'migasfree:watch:stats:hours:%04d%02d%02d%02d' % (
                    self.created_at.year, self.created_at.month,
                    self.created_at.day, self.created_at.hour
                ),
                self.computer.id
            )
            con.incr('migasfree:stats:%d:hours:%04d%02d%02d%02d' % (
                self.project.id, self.created_at.year, self.created_at.month,
                self.created_at.day, self.created_at.hour
            ))
            con.sadd(
                'migasfree:watch:stats:%d:hours:%04d%02d%02d%02d' % (
                    self.project.id, self.created_at.year, self.created_at.month,
                    self.created_at.day, self.created_at.hour
                ),
                self.computer.id
            )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)

        self.computer.sync_end_date = self.created_at
        self.computer.save()

        deployments = Deployment.available_deployments(
            self.computer, self.computer.get_all_attributes()
        ).values_list('id', flat=True)

        con = get_redis_connection()
        for deploy_id in deployments:
            con.srem(
                'migasfree:deployments:{}:ok'.format(deploy_id),
                self.computer.id
            )
            con.srem(
                'migasfree:deployments:{}:error'.format(deploy_id),
                self.computer.id
            )
            con.sadd(
                'migasfree:deployments:{}:{}'.format(
                    deploy_id,
                    'ok' if self.pms_status_ok else 'error'
                ),
                self.computer.id,
            )

    class Meta:
        app_label = 'client'
        verbose_name = _('Synchronization')
        verbose_name_plural = _('Synchronizations')
        indexes = [
            models.Index(fields=['created_at']),
        ]


@receiver(post_save, sender=Synchronization)
def post_save_sync(sender, instance, created, **kwargs):
    if created:
        instance.add_to_redis()


@receiver(pre_delete, sender=Synchronization)
def pre_delete_sync(sender, instance, **kwargs):
    con = get_redis_connection()

    if con.sismember(
        'migasfree:watch:stats:years:%04d' % instance.created_at.year,
        instance.computer.id
    ):
        con.decr('migasfree:stats:years:%04d' % instance.created_at.year)
        con.srem(
            'migasfree:watch:stats:years:%04d' % instance.created_at.year,
            instance.computer.id
        )
        con.decr('migasfree:stats:%d:years:%04d' % (
            instance.project.id, instance.created_at.year
        ))
        con.srem(
            'migasfree:watch:stats:%d:years:%04d' % (
                instance.project.id, instance.created_at.year
            ),
            instance.computer.id
        )

    if con.sismember(
        'migasfree:watch:stats:months:%04d%02d' % (
            instance.created_at.year, instance.created_at.month
        ),
        instance.computer.id
    ):
        con.decr('migasfree:stats:months:%04d%02d' % (
            instance.created_at.year, instance.created_at.month
        ))
        con.srem(
            'migasfree:watch:stats:months:%04d%02d' % (
                instance.created_at.year, instance.created_at.month
            ),
            instance.computer.id
        )
        con.decr('migasfree:stats:%d:months:%04d%02d' % (
            instance.project.id, instance.created_at.year, instance.created_at.month
        ))
        con.srem(
            'migasfree:watch:stats:%d:months:%04d%02d' % (
                instance.project.id, instance.created_at.year, instance.created_at.month
            ),
            instance.computer.id
        )

    if con.sismember(
        'migasfree:watch:stats:days:%04d%02d%02d' % (
            instance.created_at.year, instance.created_at.month, instance.created_at.day
        ),
        instance.computer.id
    ):
        con.decr('migasfree:stats:days:%04d%02d%02d' % (
            instance.created_at.year, instance.created_at.month, instance.created_at.day
        ))
        con.srem(
            'migasfree:watch:stats:days:%04d%02d%02d' % (
                instance.created_at.year, instance.created_at.month, instance.created_at.day
            ),
            instance.computer.id
        )
        con.decr('migasfree:stats:%d:days:%04d%02d%02d' % (
            instance.project.id, instance.created_at.year,
            instance.created_at.month, instance.created_at.day
        ))
        con.srem(
            'migasfree:watch:stats:%d:days:%04d%02d%02d' % (
                instance.project.id, instance.created_at.year,
                instance.created_at.month, instance.created_at.day
            ),
            instance.computer.id
        )

    if con.sismember(
        'migasfree:watch:stats:hours:%04d%02d%02d%02d' % (
            instance.created_at.year, instance.created_at.month,
            instance.created_at.day, instance.created_at.hour
        ),
        instance.computer.id
    ):
        con.decr('migasfree:stats:hours:%04d%02d%02d%02d' % (
            instance.created_at.year, instance.created_at.month,
            instance.created_at.day, instance.created_at.hour
        ))
        con.srem(
            'migasfree:watch:stats:hours:%04d%02d%02d%02d' % (
                instance.created_at.year, instance.created_at.month,
                instance.created_at.day, instance.created_at.hour
            ),
            instance.computer.id
        )
        con.decr('migasfree:stats:%d:hours:%04d%02d%02d%02d' % (
            instance.project.id, instance.created_at.year, instance.created_at.month,
            instance.created_at.day, instance.created_at.hour
        ))
        con.srem(
            'migasfree:watch:stats:%d:hours:%04d%02d%02d%02d' % (
                instance.project.id, instance.created_at.year, instance.created_at.month,
                instance.created_at.day, instance.created_at.hour
            ),
            instance.computer.id
        )
