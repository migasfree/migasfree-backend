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

from datetime import datetime, timedelta

import graphene
from django.db.models import Q
from django.utils.translation import gettext as _
from graphene_django import DjangoObjectType

from migasfree.client.models import Computer
from migasfree.utils import time_horizon

from ..models import Deployment, Domain, Schedule, ScheduleDelay


class ScheduleType(DjangoObjectType):
    class Meta:
        model = Schedule
        fields = '__all__'


class DomainType(DjangoObjectType):
    class Meta:
        model = Domain
        fields = '__all__'


class DeploymentStatsType(graphene.ObjectType):
    x_labels = graphene.List(graphene.String)
    data = graphene.JSONString()


class DeploymentType(DjangoObjectType):
    class Meta:
        model = Deployment
        fields = '__all__'

    timeline = graphene.JSONString()
    delays = graphene.Field(DeploymentStatsType)
    project_id = graphene.Int()

    def resolve_project_id(self, info):
        return self.project_id

    def resolve_timeline(self, info):
        return self.timeline()

    def resolve_delays(self, info):
        deploy = self
        if not deploy.schedule:
            return None

        # Logic ported from provides_computers_by_delay
        request = info.context
        user = request.user

        rolling_date = deploy.start_date
        provided_data = []
        labels = []
        chart_data = {}

        if deploy.domain:
            q_in_domain = ~Q(sync_attributes__id__in=deploy.domain.included_attributes.all())
            q_ex_domain = Q(sync_attributes__id__in=deploy.domain.excluded_attributes.all())
        else:
            q_in_domain = Q()
            q_ex_domain = Q()

        lst_attributes = list(deploy.included_attributes.values_list('id', flat=True))

        # Base value
        value = (
            Computer.productive.scope(user.userprofile)
            .filter(Q(sync_attributes__id__in=lst_attributes) & Q(project__id=deploy.project.id))
            .exclude(Q(sync_attributes__id__in=deploy.excluded_attributes.all()))
            .exclude(q_in_domain)
            .exclude(q_ex_domain)
            .values('id')
            .distinct()
            .count()
        )

        date_format = '%Y-%m-%d'
        delays = ScheduleDelay.objects.filter(schedule__id=deploy.schedule.id).order_by('delay')
        len_delays = delays.count()

        for i, item in enumerate(delays):
            lst_att_delay = list(item.attributes.values_list('id', flat=True))

            start_horizon = datetime.strptime(str(time_horizon(rolling_date, 0)), date_format)
            if i < (len_delays - 1):
                # Next delay relative to current
                next_delay = delays[i + 1]
                end_horizon = datetime.strptime(
                    str(time_horizon(rolling_date, next_delay.delay - item.delay)), date_format
                )
            else:
                end_horizon = datetime.strptime(str(time_horizon(rolling_date, item.duration)), date_format)

            duration = 0
            # Calculate days between horizons
            days_diff = (end_horizon - start_horizon).days

            for real_days in range(0, days_diff):
                loop_date = start_horizon + timedelta(days=real_days)
                weekday = int(loop_date.strftime('%w'))  # [0(Sunday), 6]
                if weekday not in [0, 6]:
                    from django.db.models.functions import Mod

                    value += (
                        Computer.productive.scope(user.userprofile)
                        .annotate(mod_duration=Mod('id', item.duration))
                        .filter(mod_duration=duration)
                        .filter(
                            ~Q(sync_attributes__id__in=lst_attributes)
                            & Q(sync_attributes__id__in=lst_att_delay)
                            & Q(project__id=deploy.project.id)
                        )
                        .exclude(Q(sync_attributes__id__in=deploy.excluded_attributes.all()))
                        .exclude(q_in_domain)
                        .exclude(q_ex_domain)
                        .values('id')
                        .distinct()
                        .count()
                    )
                    duration += 1

                labels.append(loop_date.strftime(date_format))
                provided_data.append({'value': value})

            lst_attributes += lst_att_delay
            rolling_date = end_horizon.date()

        chart_data[_('Provided')] = provided_data

        return DeploymentStatsType(x_labels=list(labels), data=chart_data)
