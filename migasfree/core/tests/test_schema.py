import json
from datetime import date

from graphene_django.utils.testing import GraphQLTestCase

from migasfree.client.models import Computer
from migasfree.core.models import Deployment, Project, Schedule, ScheduleDelay, UserProfile
from migasfree.schema import schema


class SchemaTestCase(GraphQLTestCase):
    GRAPHQL_SCHEMA = schema

    def setUp(self):
        self.user = UserProfile.objects.create(
            username='admin',
            email='admin@localhost.com',
            password='admin',
            is_superuser=True,
            is_staff=True,
            is_active=True,
        )
        self.client.login(username='admin', password='admin')

        from migasfree.core.models import Platform

        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(
            name='TestProject', platform=self.platform, pms='migasfree.pms.apt.Apt', architecture='amd64'
        )
        self.schedule = Schedule.objects.create(name='TestSchedule')
        self.delay = ScheduleDelay.objects.create(schedule=self.schedule, delay=0, duration=1)

        self.deployment = Deployment.objects.create(
            name='TestDeployment', project=self.project, schedule=self.schedule, start_date=date.today()
        )

        self.computer = Computer.objects.create(name='TestComputer', project=self.project, uuid='test-uuid')

    def test_deployment_query(self):
        response = self.query(
            f"""
            query {{
                deployment(id: "{self.deployment.id}") {{
                    id
                    name
                    project {{
                        name
                    }}
                    delays {{
                        xLabels
                        data
                    }}
                }}
            }}
            """
        )

        content = json.loads(response.content)
        self.assertResponseNoErrors(response)

        data = content['data']['deployment']
        self.assertEqual(data['name'], 'TestDeployment')
        self.assertEqual(data['project']['name'], 'TestProject')
        self.assertIsNotNone(data['delays'])
        self.assertIn('xLabels', data['delays'])
