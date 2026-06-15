# Copyright (c) 2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2026 Alberto Gacías <alberto@migasfree.org>
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

from rest_framework import routers

from .views import BuildViewSet, ConfigViewSet, FlavourViewSet, ReleaseViewSet

router = routers.DefaultRouter()
router.register(r'config', ConfigViewSet)
router.register(r'flavour', FlavourViewSet)
router.register(r'release', ReleaseViewSet)
router.register(r'build', BuildViewSet)

urlpatterns = [
    *router.urls,
]
