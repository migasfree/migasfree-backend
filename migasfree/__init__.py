# -*- coding: utf-8 -*-

# Copyright (c) 2015-2024 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2024 Alberto Gacías <alberto@migasfree.org>
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

from .celery import app as celery_app

__version__ = "5.0"
__author__ = [
    'Alberto Gacías <alberto@migasfree.org>',
    'Jose Antonio Chavarría <jachavar@gmail.com>'
]
__contact__ = "fun.with@migasfree.org"
__homepage__ = "https://github.com/migasfree/migasfree-backend/"

__all__ = ['celery_app']
