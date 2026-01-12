from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.core.models import UserProfile
from migasfree.device.models import Capability


class TestCapabilityViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.capability = Capability.objects.create(name='Color')

    def test_list_capabilities(self):
        response = self.client.get(reverse('capability-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
        self.assertEqual(response.json()['results'][0]['id'], self.capability.id)

    def test_retrieve_capability(self):
        response = self.client.get(reverse('capability-detail', kwargs={'pk': self.capability.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], self.capability.name)

    def test_create_capability(self):
        data = {'name': 'Duplex'}
        response = self.client.post(reverse('capability-list'), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], data['name'])

    def test_update_capability(self):
        data = {'name': 'Monochrome'}
        response = self.client.patch(reverse('capability-detail', kwargs={'pk': self.capability.pk}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], data['name'])

    def test_delete_capability(self):
        response = self.client.delete(reverse('capability-detail', kwargs={'pk': self.capability.pk}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Capability.objects.filter(pk=self.capability.pk).exists())
