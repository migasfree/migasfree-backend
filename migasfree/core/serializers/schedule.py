# Copyright (c) 2015-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2026 Alberto Gacías <alberto@migasfree.org>
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

"""
Schedule serializers.
"""

from rest_framework import serializers

from ..models import Schedule, ScheduleDelay
from .property import AttributeSerializer


class ScheduleInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ('id', 'name')


class ScheduleDelaySerializer(serializers.ModelSerializer):
    attributes = AttributeSerializer(many=True)
    schedule = ScheduleInfoSerializer(many=False, read_only=True)

    class Meta:
        model = ScheduleDelay
        fields = ('id', 'delay', 'duration', 'attributes', 'schedule')


class ScheduleDelayWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleDelay
        fields = '__all__'


class ScheduleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = '__all__'


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ('id', 'name', 'description', 'delays_count')
