# -*- coding: utf-8 *-*

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

from django.conf.urls import patterns, include, url

from .views import (
    PackagerKeysView, ProjectKeysView, SafeSynchronizationView
)

keys_patterns = patterns('',
    url(r'^packager/$', PackagerKeysView.as_view()),
    url(r'^project/$', ProjectKeysView.as_view()),
)

public_patterns = patterns('',
    url(r'keys/', include(keys_patterns)),
)

safe_patterns = patterns('',
    url(r'^synchronization/$', SafeSynchronizationView.as_view())
)

urlpatterns = patterns('',
    url(r'public/', include(public_patterns)),
    url(r'safe/', include(safe_patterns)),
    # url(r'token/', include(token_patterns)),
)
