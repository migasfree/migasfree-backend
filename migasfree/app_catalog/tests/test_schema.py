import json

from graphene_django.utils.testing import GraphQLTestCase

from migasfree.app_catalog.models import Application, Category
from migasfree.schema import schema


class AppCatalogSchemaTestCase(GraphQLTestCase):
    GRAPHQL_SCHEMA = schema

    def setUp(self):
        self.category = Category.objects.create(name='TestCategory')
        self.application = Application.objects.create(
            name='TestApp',
            description='Test App Description',
            category=self.category,
            level='U',
            score=1,
            icon='icon.png',
        )

    def test_application_query(self):
        response = self.query(
            f"""
            query {{
                application(id: "{self.application.id}") {{
                    id
                    name
                    description
                    level
                    score
                    category {{
                        name
                    }}
                }}
            }}
            """
        )

        content = json.loads(response.content)
        self.assertResponseNoErrors(response)

        data = content['data']['application']
        self.assertEqual(data['name'], 'TestApp')
        self.assertEqual(data['category']['name'], 'TestCategory')

    def test_all_categories_query(self):
        response = self.query(
            """
            query {
                allCategories {
                    id
                    name
                }
            }
            """
        )

        content = json.loads(response.content)
        self.assertResponseNoErrors(response)

        data = content['data']['allCategories']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'TestCategory')
