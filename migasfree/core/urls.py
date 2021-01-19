# -*- coding: utf-8 *-*

# Copyright (c) 2018-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2018-2021 Alberto Gacías <alberto@migasfree.org>
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

from django.conf.urls import include
from django.urls import re_path

from .views import (
    ServerInfoView, GetSourceFileView,
    PmsView, ProgrammingLanguagesView,
)

public_patterns = [
    re_path(r'server/info/', ServerInfoView.as_view()),
    re_path(r'^src/', GetSourceFileView.as_view()),
    re_path(r'pms/', PmsView.as_view()),
    re_path(r'languages', ProgrammingLanguagesView.as_view()),
]

urlpatterns = [
    re_path(r'public/', include(public_patterns)),
]
