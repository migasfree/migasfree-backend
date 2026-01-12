import graphene

import migasfree.client.schema
import migasfree.core.schema


class Query(migasfree.core.schema.Query, migasfree.client.schema.Query, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query)
