from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.core.models import UserProfile


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.db',
)
class TestCatalogView(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

    @patch('requests.get')
    def test_get_catalog_success(self, mock_get):
        # Mock successful manager response
        mock_response = mock_get.return_value
        mock_response.ok = True
        mock_response.status_code = status.HTTP_200_OK
        mock_response.json.return_value = {
            'templates': [
                {'id': 'debian-12-desktop', 'base_os': 'debian'},
                {'id': 'ubuntu-24.04-server', 'base_os': 'ubuntu'},
            ]
        }

        url = reverse('mgi-catalog')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), mock_response.json.return_value)
        mock_get.assert_called_once_with(
            'http://manager:8080/manager/v1/internal/mgi/catalog', headers={}, timeout=15.0
        )

    @patch('requests.get')
    def test_get_catalog_failure(self, mock_get):
        # Mock failed manager response
        mock_response = mock_get.return_value
        mock_response.ok = False
        mock_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        mock_response.text = 'Internal error on manager'

        url = reverse('mgi-catalog')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.json()['error'], 'Manager responded with HTTP 500')
        self.assertEqual(response.json()['details'], 'Internal error on manager')

    @patch('requests.get')
    def test_get_catalog_exception(self, mock_get):
        # Mock exception connecting to manager
        mock_get.side_effect = Exception('Connection refused')

        url = reverse('mgi-catalog')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('Could not connect to manager: Connection refused', response.json()['error'])

    def test_get_catalog_unauthorized(self):
        self.client.force_authenticate(user=None)
        url = reverse('mgi-catalog')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
