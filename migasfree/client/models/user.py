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


@python_2_unicode_compatible
class User(models.Model):
    name = models.CharField(
        verbose_name=_("name"),
        max_length=50,
        null=False
    )

    fullname = models.CharField(
        verbose_name=_("fullname"),
        max_length=100,
        blank=True
    )

    def __str__(self):
        if self.fullname != '':
            return '%s (%s)' % (self.name, self.fullname)

        return self.name

    class Meta:
        app_label = 'client'
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        unique_together = (('name', 'fullname'),)
