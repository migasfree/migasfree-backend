# -*- coding: utf-8 -*-

# Copyright (c) 2015-2017 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2017 Alberto Gacías <alberto@migasfree.org>
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


class NotificationQueryset(models.query.QuerySet):
    def unchecked(self):
        return self.filter(checked=False)


class NotificationManager(models.Manager):
    def get_queryset(self):
        return NotificationQueryset(self.model, using=self._db)

    def unchecked(self):
        return self.get_queryset().unchecked()


@python_2_unicode_compatible
class Notification(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("date"),
    )

    message = models.TextField(
        verbose_name=_("message"),
    )

    checked = models.BooleanField(
        verbose_name=_("checked"),
        default=False,
    )

    objects = NotificationManager()

    def checked_ok(self):
        self.checked = True
        self.save()

    def save(self, *args, **kwargs):
        self.message = self.message.replace("\r\n", "\n")
        super(Notification, self).save(*args, **kwargs)

    def __str__(self):
        return '{} ({:%Y-%m-%d %H:%M:%S})'.format(self.id, self.created_at)

    class Meta:
        app_label = 'client'
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
