import graphene

from graphene_django.types import DjangoObjectType

from .models import Computer, Error


class ComputerType(DjangoObjectType):
    class Meta:
        model = Computer


class ErrorType(DjangoObjectType):
    class Meta:
        model = Error


class Query:
    all_computers = graphene.List(ComputerType)
    all_errors = graphene.List(ErrorType)

    def resolve_all_computers(self, info, **kwargs):
        return Computer.objects.all()

    def resolve_all_errors(self, info, **kwargs):
        # We can easily optimize query count in the resolve method
        return Error.objects.select_related('computer').all()
