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

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_redis import get_redis_connection

from migasfree.core.models import Project, Deployment

from .event import Event
from .user import User


class Synchronization(Event):
    start_date = models.DateTimeField(
        verbose_name=_('start date connection'),
        null=True,
        blank=True
    )

    user = models.ForeignKey(
        User,
        verbose_name=_("user")
    )

    project = models.ForeignKey(
        Project,
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

    def save(self, *args, **kwargs):
        super(Synchronization, self).save(*args, **kwargs)

        self.computer.sync_end_date = self.created_at
        self.computer.save()

        deployments = Deployment.available_deployments(
            self.computer, self.computer.get_all_attributes()
        ).values_list('id', flat=True)

        con = get_redis_connection('default')
        for deploy_id in deployments:
            con.sadd(
                'migasfree:deployments:%d:%s' % (
                    deploy_id,
                    'ok' if self.pms_status_ok else 'error'
                ),
                self.computer.id,
            )

    class Meta:
        app_label = 'client'
        verbose_name = _("Synchronization")
        verbose_name_plural = _("Synchronizations")
