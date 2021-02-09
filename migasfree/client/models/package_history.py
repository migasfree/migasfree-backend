# -*- coding: utf-8 -*-

# Copyright (c) 2017-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2017-2021 Alberto Gacías <alberto@migasfree.org>
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
from django.utils.translation import gettext_lazy as _

from ...core.models import Package, MigasLink
from .computer import Computer


class PackageHistory(models.Model, MigasLink):
    """packages installed or/and uninstalled in computers"""

    computer = models.ForeignKey(
        Computer,
        on_delete=models.CASCADE,
        verbose_name=_('computer')
    )

    package = models.ForeignKey(
        Package,
        on_delete=models.CASCADE,
        verbose_name=_('package')
    )

    install_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('install date'),
        null=True,
    )

    uninstall_date = models.DateTimeField(
        verbose_name=_('uninstall date'),
        null=True,
    )

    def __str__(self):
        return _('%s at computer %s') % (self.package.fullname, self.computer)

    class Meta:
        app_label = 'client'
        verbose_name = 'Package History'
        verbose_name_plural = 'Packages History'
