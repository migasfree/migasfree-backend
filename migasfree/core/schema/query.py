# Copyright (c) 2019-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2019-2026 Alberto Gacías <alberto@migasfree.org>
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

import graphene
from graphene_django import DjangoObjectType

from migasfree.core.models import Deployment, Domain, Platform, Project, Schedule
from migasfree.core.schema.deployment import DeploymentType, DomainType, ScheduleType
from migasfree.core.schema.project import ProjectType


class PlatformType(DjangoObjectType):
    class Meta:
        model = Platform


class Query:
    all_platforms = graphene.List(PlatformType)
    all_projects = graphene.List(ProjectType)
    project = graphene.Field(ProjectType, id=graphene.ID())
    deployment = graphene.Field(DeploymentType, id=graphene.ID())
    all_deployments = graphene.List(DeploymentType)
    all_schedules = graphene.List(ScheduleType)
    all_domains = graphene.List(DomainType)

    def resolve_all_platforms(self, info, **kwargs):
        return Platform.objects.all()

    def resolve_all_projects(self, info, **kwargs):
        return Project.objects.select_related('platform').all()

    def resolve_project(self, info, id):
        return Project.objects.get(pk=id)

    def resolve_deployment(self, info, id):
        return Deployment.objects.get(pk=id)

    def resolve_all_deployments(self, info, **kwargs):
        return Deployment.objects.select_related('project', 'schedule', 'domain').all()

    def resolve_all_schedules(self, info, **kwargs):
        return Schedule.objects.all()

    def resolve_all_domains(self, info, **kwargs):
        return Domain.objects.all()
