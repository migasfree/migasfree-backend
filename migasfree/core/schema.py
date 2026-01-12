import graphene
from graphene_django.types import DjangoObjectType

from .models import Platform, Project


class PlatformType(DjangoObjectType):
    class Meta:
        model = Platform


class ProjectType(DjangoObjectType):
    class Meta:
        model = Project


class Query:
    all_platforms = graphene.List(PlatformType)
    all_projects = graphene.List(ProjectType)

    def resolve_all_platforms(self, info, **kwargs):
        return Platform.objects.all()

    def resolve_all_projects(self, info, **kwargs):
        # We can easily optimize query count in the resolve method
        return Project.objects.select_related('platform').all()
