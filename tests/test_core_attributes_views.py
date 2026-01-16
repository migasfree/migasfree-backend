from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.core.models import (
    Attribute,
    AttributeSet,
    ClientAttribute,
    ClientProperty,
    Platform,
    Project,
    Property,
    ServerAttribute,
    ServerProperty,
    Singularity,
    UserProfile,
)


class TestPropertyViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.property = Property.objects.create(name='Test Property', prefix='TST')

    def test_list_properties(self):
        response = self.client.get(reverse('property-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)

    def test_retrieve_property(self):
        response = self.client.get(reverse('property-detail', kwargs={'pk': self.property.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], self.property.name)

    def test_create_property(self):
        data = {'name': 'New Property', 'prefix': 'NEW', 'kind': 'N'}
        response = self.client.post(reverse('property-list'), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], data['name'])

    def test_update_property(self):
        data = {'name': 'Updated Property'}
        response = self.client.patch(reverse('property-detail', kwargs={'pk': self.property.pk}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], data['name'])

    def test_kind_action(self):
        response = self.client.get(reverse('property-kind'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)


class TestServerPropertyViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.property = ServerProperty.objects.create(name='Server Property', prefix='SRV', sort='server')

    def test_list_server_properties(self):
        response = self.client.get(reverse('serverproperty-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)


class TestClientPropertyViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.property = ClientProperty.objects.create(name='Client Property', prefix='CLT', sort='client')

    def test_list_client_properties(self):
        response = self.client.get(reverse('clientproperty-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)


class TestAttributeViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.property_att = Property.objects.create(name='Test Property', prefix='TST')
        self.attribute = Attribute.objects.create(property_att=self.property_att, value='value1')

    def test_list_attributes(self):
        response = self.client.get(reverse('attribute-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)

    def test_retrieve_attribute(self):
        response = self.client.get(reverse('attribute-detail', kwargs={'pk': self.attribute.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['value'], self.attribute.value)


class TestServerAttributeViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.property = ServerProperty.objects.create(name='Server Property', prefix='SRV', sort='server')
        self.attribute = ServerAttribute.objects.create(property_att=self.property, value='tag1')

    def test_list_server_attributes(self):
        response = self.client.get(reverse('serverattribute-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)

    def test_retrieve_server_attribute(self):
        response = self.client.get(reverse('serverattribute-detail', kwargs={'pk': self.attribute.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['value'], self.attribute.value)

    def test_create_server_attribute(self):
        data = {'property_att': self.property.pk, 'value': 'newtag'}
        response = self.client.post(reverse('serverattribute-list'), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['value'], data['value'])


class TestClientAttributeViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.property = ClientProperty.objects.create(name='Client Property', prefix='CLT', sort='client')
        self.attribute = ClientAttribute.objects.create(property_att=self.property, value='feature1')

    def test_list_client_attributes(self):
        response = self.client.get(reverse('clientattribute-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)

    def test_retrieve_client_attribute(self):
        response = self.client.get(reverse('clientattribute-detail', kwargs={'pk': self.attribute.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['value'], self.attribute.value)


class TestAttributeSetViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        # Required for AttributeSet.save() to work
        Property.objects.create(name='Attribute Sets', prefix='SET', sort='basic')

        self.property_att = Property.objects.create(name='Test Property', prefix='TST')
        self.attribute = Attribute.objects.create(property_att=self.property_att, value='value1')

        self.attribute_set = AttributeSet.objects.create(name='Test Set')
        self.attribute_set.included_attributes.add(self.attribute)

    def test_list_attribute_sets(self):
        response = self.client.get(reverse('attributeset-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)

    def test_retrieve_attribute_set(self):
        response = self.client.get(reverse('attributeset-detail', kwargs={'pk': self.attribute_set.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], self.attribute_set.name)

    def test_create_attribute_set(self):
        data = {
            'name': 'New Attribute Set',
            'included_attributes': [self.attribute.pk],
            'excluded_attributes': [],
        }
        response = self.client.post(reverse('attributeset-list'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], data['name'])


class TestSingularityViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.property = Property.objects.create(name='Singularity Property', prefix='SNG')
        self.attribute = Attribute.objects.create(property_att=self.property, value='val1')

        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(
            name='TestProject', pms='apt', architecture='amd64', platform=self.platform
        )

        self.singularity = Singularity.objects.create(name='Test Singularity', property_att=self.property, priority=1)
        self.singularity.included_attributes.add(self.attribute)

    def test_list_singularities(self):
        response = self.client.get(reverse('singularity-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)

    def test_retrieve_singularity(self):
        response = self.client.get(reverse('singularity-detail', kwargs={'pk': self.singularity.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], self.singularity.name)

    def test_create_singularity(self):
        data = {
            'name': 'New Singularity',
            'property_att': self.property.pk,
            'priority': 2,
            'included_attributes': [self.attribute.pk],
            'excluded_attributes': [],
        }
        response = self.client.post(reverse('singularity-list'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], data['name'])
