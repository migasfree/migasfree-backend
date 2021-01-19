# -*- coding: utf-8 *-*

# Copyright (c) 2015-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2021 Alberto Gacías <alberto@migasfree.org>
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
    PackagerKeysView, ProjectKeysView,
    RepositoriesKeysView,
    SafeSynchronizationView, SafeEndOfTransmissionView,
)

keys_patterns = [
    re_path(r'^packager/$', PackagerKeysView.as_view()),
    re_path(r'^project/$', ProjectKeysView.as_view()),
    re_path(r'^repositories/$', RepositoriesKeysView.as_view()),
]

public_patterns = [
    re_path(r'keys/', include(keys_patterns)),
]

safe_patterns = [
    re_path(r'^eot/$', SafeEndOfTransmissionView.as_view()),
    re_path(r'^synchronizations/$', SafeSynchronizationView.as_view()),
]

urlpatterns = [
    re_path(r'public/', include(public_patterns)),
    re_path(r'safe/', include(safe_patterns)),
    # re_path(r'token/', include(token_patterns)),
]
