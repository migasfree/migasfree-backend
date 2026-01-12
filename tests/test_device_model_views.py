from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.core.models import UserProfile
from migasfree.device.models import Connection, Manufacturer, Model, Type


class TestModelViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.device_type = Type.objects.create(name='PRINTER')
        self.manufacturer = Manufacturer.objects.create(name='HP')
        self.connection = Connection.objects.create(name='USB', device_type=self.device_type)
        self.model = Model.objects.create(
            name='LaserJet Pro', manufacturer=self.manufacturer, device_type=self.device_type
        )
        self.model.connections.set([self.connection])

    def test_list_models(self):
        response = self.client.get(reverse('model-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
        self.assertEqual(response.json()['results'][0]['id'], self.model.id)

    def test_retrieve_model(self):
        response = self.client.get(reverse('model-detail', kwargs={'pk': self.model.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], self.model.name)

    def test_create_model(self):
        data = {
            'name': 'OfficeJet',
            'manufacturer': self.manufacturer.id,
            'device_type': self.device_type.id,
            'connections': [self.connection.id],
        }
        response = self.client.post(reverse('model-list'), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], data['name'])

    def test_update_model(self):
        data = {'name': 'LaserJet Enterprise'}
        response = self.client.patch(reverse('model-detail', kwargs={'pk': self.model.pk}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Model replaces spaces with underscores in name
        self.assertEqual(response.json()['name'], 'LaserJet_Enterprise')

    def test_delete_model(self):
        response = self.client.delete(reverse('model-detail', kwargs={'pk': self.model.pk}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Model.objects.filter(pk=self.model.pk).exists())

    def test_search_model(self):
        response = self.client.get(reverse('model-list'), {'search': 'LaserJet'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)
