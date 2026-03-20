# Copyright (c) 2020-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2020-2026 Alberto Gacías <alberto@migasfree.org>
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

from ..services.links import MigasLinkService


class MigasLink:
    def __init__(self):
        self._actions = None
        self._exclude_links = []
        self._include_links = []

    @property
    def link_service(self):
        if not hasattr(self, '_link_service'):
            self._link_service = MigasLinkService(self)
        return self._link_service

    def relations(self, request):
        return self.link_service.relations(request)

    def get_relations(self, request):
        return self.link_service.get_relations(request)

    def badge(self):
        return self.link_service.badge()
