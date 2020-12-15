# -*- coding: utf-8 *-*

# Copyright (c) 2018-2020 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2018-2020 Alberto Gacías <alberto@migasfree.org>
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

from django.conf.urls import include, url

from .views import ServerInfoView, GetSourceFileView, PmsView

public_patterns = [
    url(r'server/info/', ServerInfoView.as_view()),
    url(r'^src/', GetSourceFileView.as_view()),
    url(r'pms/', PmsView.as_view())
]

urlpatterns = [
    url(r'public/', include(public_patterns)),
]
