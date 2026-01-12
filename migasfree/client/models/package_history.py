# Copyright (c) 2017-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2017-2026 Alberto Gacías <alberto@migasfree.org>
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
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ...core.models import MigasLink, Package
from .computer import Computer


class PackageHistoryManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                'computer',
                'package',
                'computer__project',
                'computer__sync_user',
            )
        )

    def scope(self, user):
        qs = self.get_queryset()
        if user and not user.is_view_all():
            qs = qs.filter(computer__in=user.get_computers())

        return qs


class PackageHistory(models.Model, MigasLink):
    """packages installed or/and uninstalled in computers"""

    computer = models.ForeignKey(
        Computer,
        on_delete=models.CASCADE,
        verbose_name=_('computer'),
        db_comment='related computer',
    )

    package = models.ForeignKey(
        Package,
        on_delete=models.CASCADE,
        verbose_name=_('package'),
        db_comment='related package',
    )

    install_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('install date'),
        null=True,
        db_comment='date the package was installed on the computer',
    )

    uninstall_date = models.DateTimeField(
        verbose_name=_('uninstall date'),
        null=True,
        db_comment='date of uninstallation of the package on the computer',
    )

    objects = PackageHistoryManager()

    def __str__(self):
        return _('%s at computer %s') % (self.package.fullname, self.computer)

    @staticmethod
    def uninstall_computer_packages(computer_id):
        if computer_id is None:
            raise ValueError('Invalid computer_id')

        PackageHistory.objects.filter(computer__id=computer_id, uninstall_date=None).update(
            uninstall_date=timezone.localtime(timezone.now())
        )

    class Meta:
        app_label = 'client'
        verbose_name = _('Package History')
        verbose_name_plural = _('Packages History')
        db_table_comment = 'history of changes to the computer packages'
