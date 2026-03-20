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

import graphene
from graphene_django import DjangoObjectType

from migasfree.app_catalog.models import (
    Application,
    Category,
    PackagesByProject,
    Policy,
    PolicyGroup,
)


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = '__all__'


class ApplicationType(DjangoObjectType):
    class Meta:
        model = Application
        fields = '__all__'


class PackagesByProjectType(DjangoObjectType):
    class Meta:
        model = PackagesByProject
        fields = '__all__'


class PolicyType(DjangoObjectType):
    class Meta:
        model = Policy
        fields = '__all__'


class PolicyGroupType(DjangoObjectType):
    class Meta:
        model = PolicyGroup
        fields = '__all__'


class Query:
    all_categories = graphene.List(CategoryType)
    category = graphene.Field(CategoryType, id=graphene.ID())

    all_applications = graphene.List(ApplicationType)
    application = graphene.Field(ApplicationType, id=graphene.ID())

    all_packages_by_projects = graphene.List(PackagesByProjectType)
    packages_by_project = graphene.Field(PackagesByProjectType, id=graphene.ID())

    all_policies = graphene.List(PolicyType)
    policy = graphene.Field(PolicyType, id=graphene.ID())

    all_policy_groups = graphene.List(PolicyGroupType)
    policy_group = graphene.Field(PolicyGroupType, id=graphene.ID())

    def resolve_all_categories(self, info, **kwargs):
        return Category.objects.all()

    def resolve_category(self, info, id):
        return Category.objects.get(pk=id)

    def resolve_all_applications(self, info, **kwargs):
        return Application.objects.select_related('category').prefetch_related('available_for_attributes').all()

    def resolve_application(self, info, id):
        return Application.objects.select_related('category').prefetch_related('available_for_attributes').get(pk=id)

    def resolve_all_packages_by_projects(self, info, **kwargs):
        return PackagesByProject.objects.select_related('application', 'project').all()

    def resolve_packages_by_project(self, info, id):
        return PackagesByProject.objects.select_related('application', 'project').get(pk=id)

    def resolve_all_policies(self, info, **kwargs):
        return Policy.objects.prefetch_related('included_attributes', 'excluded_attributes').all()

    def resolve_policy(self, info, id):
        return Policy.objects.prefetch_related('included_attributes', 'excluded_attributes').get(pk=id)

    def resolve_all_policy_groups(self, info, **kwargs):
        return (
            PolicyGroup.objects.select_related('policy')
            .prefetch_related('included_attributes', 'excluded_attributes', 'applications')
            .all()
        )

    def resolve_policy_group(self, info, id):
        return (
            PolicyGroup.objects.select_related('policy')
            .prefetch_related('included_attributes', 'excluded_attributes', 'applications')
            .get(pk=id)
        )
