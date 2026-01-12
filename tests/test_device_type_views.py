from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.core.models import UserProfile
from migasfree.device.models import Type


class TestTypeViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.device_type = Type.objects.create(name='PRINTER')

    def test_list_types(self):
        response = self.client.get(reverse('type-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
        self.assertEqual(response.json()['results'][0]['id'], self.device_type.id)

    def test_retrieve_type(self):
        response = self.client.get(reverse('type-detail', kwargs={'pk': self.device_type.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['id'], self.device_type.id)
        self.assertEqual(response.json()['name'], self.device_type.name)

    def test_create_type(self):
        data = {'name': 'SCANNER'}
        response = self.client.post(reverse('type-list'), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], data['name'])
        self.assertEqual(Type.objects.count(), 2)

    def test_update_type(self):
        data = {'name': 'MULTIFUNCTION'}
        response = self.client.patch(reverse('type-detail', kwargs={'pk': self.device_type.pk}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], data['name'])

    def test_delete_type(self):
        response = self.client.delete(reverse('type-detail', kwargs={'pk': self.device_type.pk}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Type.objects.filter(pk=self.device_type.pk).exists())

    def test_search_type(self):
        response = self.client.get(reverse('type-list'), {'search': 'PRINT'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)
