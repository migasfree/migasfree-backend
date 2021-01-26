# -*- coding: utf-8 -*-

# Copyright (c) 2017-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2017-2021 Alberto Gacías <alberto@migasfree.org>
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

import django_filters

from .models import Application, PackagesByProject, Policy


class ApplicationFilter(django_filters.FilterSet):
    class Meta:
        model = Application
        fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains'],
            'level': ['exact'],
            'category': ['exact'],
            'score': ['exact']
        }


class PackagesByProjectFilter(django_filters.FilterSet):
    packages_to_install = django_filters.CharFilter(
        field_name='packages_to_install', lookup_expr='icontains'
    )

    class Meta:
        model = PackagesByProject
        fields = {
            'application__id': ['exact'],
            'project__id': ['exact'],
            'project__name': ['exact', 'icontains'],
        }


class PolicyFilter(django_filters.FilterSet):
    class Meta:
        model = Policy
        fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains'],
            'enabled': ['exact'],
            'exclusive': ['exact'],
        }
