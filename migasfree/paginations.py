# -*- coding: utf-8 -*-

# Copyright (c) 2020 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2020 Alberto Gacías <alberto@migasfree.org>
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

from rest_framework import pagination


class DefaultPagination(pagination.PageNumberPagination):
    page_size = 100
    max_page_size = 10000
    page_size_query_param = 'page_size'
