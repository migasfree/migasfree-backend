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

from rest_framework import permissions, viewsets
from rest_framework.decorators import permission_classes

from ....core.views import ExportViewSet, MigasViewSet
from ....mixins import DatabaseCheckMixin


@permission_classes((permissions.DjangoModelPermissions,))
class BaseClientViewSet(
    DatabaseCheckMixin,
    viewsets.GenericViewSet,
    MigasViewSet,
    ExportViewSet,
):
    ordering_fields = '__all__'

    def get_queryset(self):
        if self.request is None:
            return self.queryset.model.objects.none()

        return self.queryset.model.objects.scope(self.request.user.userprofile)
