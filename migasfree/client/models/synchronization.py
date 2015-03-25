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

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible
from django_redis import get_redis_connection

from migasfree.core.models import Project, Release

from .computer import Computer
from .user import User


@python_2_unicode_compatible
class Synchronization(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    start_date = models.DateTimeField(
        verbose_name=_('start date connection'),
        null=True,
        blank=True
    )

    computer = models.ForeignKey(
        Computer,
        verbose_name=_("computer")
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

        releases = Release.available_repos(
            self.computer.project.id, self.computer.get_all_attributes()
        ).values_list('id', flat=True)

        con = get_redis_connection('default')
        for release_id in releases:
            con.sadd(
                'migasfree:releases:%d:%s' % (
                    release_id,
                    'ok' if self.pms_status_ok else 'error'
                ),
                self.computer.id,
            )

    def __str__(self):
        return '%s %s' % (self.computer.__str__(), self.created_at)

    class Meta:
        app_label = 'client'
        verbose_name = _("Synchronization")
        verbose_name_plural = _("Synchronizations")
