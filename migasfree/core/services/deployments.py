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

import datetime
from django.utils import timezone

from ...utils import time_horizon


class DeploymentTimelineService:
    @staticmethod
    def get_percent(begin_date, end_date):
        delta = end_date - begin_date
        aware_date = timezone.make_aware(
            datetime.datetime.combine(begin_date, datetime.datetime.min.time()), timezone.get_default_timezone()
        )
        progress = timezone.localtime(timezone.now()) - aware_date

        if delta.days > 0:
            percent = float(progress.days) / delta.days * 100
            if percent > 100:
                percent = 100
            elif percent < 0:
                percent = 0
        else:
            percent = 100

        return int(percent)

    @staticmethod
    def schedule_timeline(deployment):
        if deployment.schedule is None:
            return None

        delays = sorted(deployment.schedule.delays.all(), key=lambda x: x.delay)

        if not delays:
            return None

        begin_date = time_horizon(deployment.start_date, delays[0].delay)
        end_date = time_horizon(deployment.start_date, delays[-1].delay + delays[-1].duration)

        return {
            'begin_date': str(begin_date),
            'end_date': str(end_date),
            'percent': DeploymentTimelineService.get_percent(begin_date, end_date),
        }

    @staticmethod
    def timeline(deployment):
        from django.utils.translation import gettext as _

        schedule_timeline = DeploymentTimelineService.schedule_timeline(deployment)

        if not schedule_timeline:
            return None

        date_format = '%Y-%m-%d'
        begin_date = datetime.datetime.strptime(schedule_timeline['begin_date'], date_format)
        end_date = datetime.datetime.strptime(schedule_timeline['end_date'], date_format)

        days = (datetime.datetime.today() - begin_date).days + 1
        total_days = (end_date - begin_date).days
        return {
            'deployment_id': deployment.pk,
            'percent': schedule_timeline['percent'],
            'schedule': deployment.schedule,
            'info': _('%s/%s days (from %s to %s)')
            % (days, total_days, schedule_timeline['begin_date'], schedule_timeline['end_date']),
        }
