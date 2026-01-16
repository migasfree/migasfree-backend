from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.core.models import (
    Attribute,
    Deployment,
    ExternalSource,
    InternalSource,
    Platform,
    Project,
    Property,
    Schedule,
    Store,
    UserProfile,
)


class TestDeploymentViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(name='Vitalinux', pms='apt', architecture='amd64', platform=self.platform)

        self.property_att = Property.objects.create(name='Test Property', prefix='TST')
        self.attribute = Attribute.objects.create(property_att=self.property_att, value='value1')

        self.schedule = Schedule.objects.create(name='Default Schedule')

        self.deployment = Deployment.objects.create(
            name='Test Deployment',
            project=self.project,
            enabled=True,
        )
        self.deployment.included_attributes.add(self.attribute)

    def test_list_deployments(self):
        response = self.client.get(reverse('deployment-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
        self.assertGreaterEqual(response.json()['count'], 1)

    def test_retrieve_deployment(self):
        response = self.client.get(reverse('deployment-detail', kwargs={'pk': self.deployment.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], self.deployment.name)

    def test_create_deployment(self):
        data = {
            'name': 'New Deployment',
            'project': self.project.pk,
            'enabled': True,
            'included_attributes': [self.attribute.pk],
            'excluded_attributes': [],
        }
        response = self.client.post(reverse('deployment-list'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], data['name'])

    def test_update_deployment(self):
        data = {'name': 'Updated Deployment'}
        response = self.client.patch(reverse('deployment-detail', kwargs={'pk': self.deployment.pk}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], data['name'])

    def test_search_deployment(self):
        response = self.client.get(reverse('deployment-list'), {'search': 'Test'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.json()['count'], 1)

    def test_filter_deployment_by_project(self):
        response = self.client.get(reverse('deployment-list'), {'project__id': self.project.pk})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.json()['count'], 1)


class TestInternalSourceViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(name='Vitalinux', pms='apt', architecture='amd64', platform=self.platform)
        self.store = Store.objects.create(name='Main Store', project=self.project)

        self.property_att = Property.objects.create(name='Test Property', prefix='TST')
        self.attribute = Attribute.objects.create(property_att=self.property_att, value='value1')

        self.internal_source = InternalSource.objects.create(
            name='Test Internal Source',
            project=self.project,
            enabled=True,
        )
        self.internal_source.included_attributes.add(self.attribute)

    def test_list_internal_sources(self):
        response = self.client.get(reverse('internalsource-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
        self.assertGreaterEqual(response.json()['count'], 1)

    def test_retrieve_internal_source(self):
        response = self.client.get(reverse('internalsource-detail', kwargs={'pk': self.internal_source.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], self.internal_source.name)

    def test_create_internal_source(self):
        data = {
            'name': 'New Internal Source',
            'project': self.project.pk,
            'enabled': True,
            'included_attributes': [self.attribute.pk],
            'excluded_attributes': [],
        }
        response = self.client.post(reverse('internalsource-list'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], data['name'])


class TestExternalSourceViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(name='Vitalinux', pms='apt', architecture='amd64', platform=self.platform)

        self.property_att = Property.objects.create(name='Test Property', prefix='TST')
        self.attribute = Attribute.objects.create(property_att=self.property_att, value='value1')

        self.external_source = ExternalSource.objects.create(
            name='Test External Source',
            project=self.project,
            enabled=True,
            base_url='http://example.com/repo',
        )
        self.external_source.included_attributes.add(self.attribute)

    def test_list_external_sources(self):
        response = self.client.get(reverse('externalsource-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
        self.assertGreaterEqual(response.json()['count'], 1)

    def test_retrieve_external_source(self):
        response = self.client.get(reverse('externalsource-detail', kwargs={'pk': self.external_source.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], self.external_source.name)

    def test_create_external_source(self):
        data = {
            'name': 'New External Source',
            'project': self.project.pk,
            'enabled': True,
            'base_url': 'http://newexample.com/repo',
            'included_attributes': [self.attribute.pk],
            'excluded_attributes': [],
        }
        response = self.client.post(reverse('externalsource-list'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], data['name'])
