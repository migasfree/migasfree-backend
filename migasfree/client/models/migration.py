# -*- coding: utf-8 *-*

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

from migasfree.core.models import Project

from .event import Event


@python_2_unicode_compatible
class Migration(Event):
    project = models.ForeignKey(
        Project,
        verbose_name=_("project")
    )

    def __str__(self):
        return u'{} ({:%Y-%m-%d %H:%M:%S}) {}'.format(
            self.computer, self.created_at, self.project
        )

    class Meta:
        app_label = 'client'
        verbose_name = _("Migration")
        verbose_name_plural = _("Migrations")
