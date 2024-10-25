from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.core.models import UserProfile
from migasfree.device.models import Connection, Type


class TestConnectionViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.device_type = Type.objects.create(name='PRINTER')
        self.connection = Connection.objects.create(name='USB', device_type=self.device_type)

    def test_list_connections(self):
        response = self.client.get(reverse('connection-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
        self.assertEqual(response.json()['results'][0]['id'], self.connection.id)

    def test_retrieve_connection(self):
        response = self.client.get(reverse('connection-detail', kwargs={'pk': self.connection.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
        self.assertEqual(response.json()['id'], self.connection.id)

    def test_create_connection(self):
        data = {
            'name': 'SRL',
            'device_type': self.device_type.id
        }
        response = self.client.post(reverse('connection-list'), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsInstance(response.json(), dict)
        self.assertEqual(response.json()['name'], data['name'])

    def test_update_connection(self):
        data = {
            'name': 'LPT'
        }
        response = self.client.patch(reverse('connection-detail', kwargs={'pk': self.connection.pk}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
        self.assertEqual(response.json()['name'], data['name'])

    def test_delete_connection(self):
        response = self.client.delete(reverse('connection-detail', kwargs={'pk': self.connection.pk}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Connection.objects.filter(pk=self.connection.pk).exists())

    def test_create_update_destroy(self):
        response = self.client.post(reverse('connection-list'), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsInstance(response.json(), dict)

        response = self.client.patch(reverse('connection-detail', kwargs={'pk': self.connection.pk}), {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)

        response = self.client.delete(reverse('connection-detail', kwargs={'pk': self.connection.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Connection.objects.filter(pk=self.connection.pk).exists())

    def test_filtering(self):
        response = self.client.get(reverse('connection-list'), {'name': self.connection.name})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
        self.assertEqual(response.json()['results'][0]['id'], self.connection.id)
        self.assertEqual(response.json()['results'][0]['name'], self.connection.__str__())
