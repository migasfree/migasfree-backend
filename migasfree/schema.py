import graphene
import migasfree.core.schema
import migasfree.client.schema


class Query(migasfree.core.schema.Query, migasfree.client.schema.Query, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query)
