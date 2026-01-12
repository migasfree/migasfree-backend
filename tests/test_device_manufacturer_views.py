from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.core.models import UserProfile
from migasfree.device.models import Manufacturer


class TestManufacturerViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.manufacturer = Manufacturer.objects.create(name='HP')

    def test_list_manufacturers(self):
        response = self.client.get(reverse('manufacturer-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
        self.assertEqual(response.json()['results'][0]['id'], self.manufacturer.id)

    def test_retrieve_manufacturer(self):
        response = self.client.get(reverse('manufacturer-detail', kwargs={'pk': self.manufacturer.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], self.manufacturer.name)

    def test_create_manufacturer(self):
        data = {'name': 'Canon'}
        response = self.client.post(reverse('manufacturer-list'), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], data['name'])

    def test_update_manufacturer(self):
        data = {'name': 'Hewlett Packard'}
        response = self.client.patch(reverse('manufacturer-detail', kwargs={'pk': self.manufacturer.pk}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], data['name'])

    def test_delete_manufacturer(self):
        response = self.client.delete(reverse('manufacturer-detail', kwargs={'pk': self.manufacturer.pk}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Manufacturer.objects.filter(pk=self.manufacturer.pk).exists())

    def test_search_manufacturer(self):
        response = self.client.get(reverse('manufacturer-list'), {'search': 'HP'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)
