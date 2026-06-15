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

from django_filters import rest_framework as filters

from .models import Build, Config, Flavour, Release


class ConfigFilter(filters.FilterSet):
    class Meta:
        model = Config
        fields = {
            'id': ['exact', 'in'],
            'project': ['exact', 'in'],
            'project__id': ['exact', 'in'],
            'project__name': ['exact', 'icontains'],
            'template_id': ['exact', 'icontains'],
            'build_type': ['exact', 'in'],
            'base_os': ['exact', 'icontains'],
            'image_format': ['exact', 'in'],
        }


class FlavourFilter(filters.FilterSet):
    class Meta:
        model = Flavour
        fields = {
            'id': ['exact', 'in'],
            'config': ['exact', 'in'],
            'config__id': ['exact', 'in'],
            'name': ['exact', 'icontains'],
            'description': ['icontains'],
            'enabled': ['exact'],
            'hostname': ['exact', 'icontains'],
            'tags': ['exact', 'in'],
            'tags__id': ['exact', 'in'],
            'tags__value': ['exact', 'icontains'],
        }


class ReleaseFilter(filters.FilterSet):
    class Meta:
        model = Release
        fields = {
            'id': ['exact', 'in'],
            'config': ['exact', 'in'],
            'config__id': ['exact', 'in'],
            'name': ['exact', 'icontains'],
            'description': ['icontains'],
            'created_at': ['exact', 'gte', 'lte', 'gt', 'lt'],
        }


class BuildFilter(filters.FilterSet):
    class Meta:
        model = Build
        fields = {
            'id': ['exact', 'in'],
            'release': ['exact', 'in'],
            'release__id': ['exact', 'in'],
            'flavour': ['exact', 'in'],
            'flavour__id': ['exact', 'in'],
            'status': ['exact', 'in'],
            'task_id': ['exact', 'icontains'],
            'started_at': ['exact', 'gte', 'lte', 'gt', 'lt', 'isnull'],
            'finished_at': ['exact', 'gte', 'lte', 'gt', 'lt', 'isnull'],
        }
