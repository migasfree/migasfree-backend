import json

from graphene_django.utils.testing import GraphQLTestCase

from migasfree.core.models import Platform, Project
from migasfree.schema import schema


class ProjectSchemaTestCase(GraphQLTestCase):
    GRAPHQL_SCHEMA = schema

    def setUp(self):
        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(
            name='TestProject', platform=self.platform, pms='migasfree.pms.apt.Apt', architecture='amd64'
        )

    def test_project_query(self):
        response = self.query(
            f"""
            query {{
                project(id: "{self.project.id}") {{
                    id
                    name
                    platform {{
                        name
                    }}
                }}
            }}
            """
        )

        content = json.loads(response.content)
        self.assertResponseNoErrors(response)

        data = content['data']['project']
        self.assertEqual(data['name'], 'TestProject')
        self.assertEqual(data['platform']['name'], 'Linux')
