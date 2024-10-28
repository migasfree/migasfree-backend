import os

from django.conf import settings
from django.test import TestCase
from rest_framework import status

from migasfree.client.views.public import ProjectKeysView
from migasfree.core.models import UserProfile, Platform, Project


class TestPackagerKeysView(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.url = '/api/v1/public/keys/packager/'

    def test_post_request(self):
        response = self.client.post(self.url, {
            'username': self.user.username,
            'password': 'test'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(settings.MIGASFREE_PUBLIC_KEY, response.data)
        self.assertIn(settings.MIGASFREE_PACKAGER_PRI_KEY, response.data)

    def test_nonexistent_user(self):
        response = self.client.post(self.url, {
            'username': 'non_existent_user',
            'password': 'password'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_credentials(self):
        response = self.client.post(self.url, {
            'username': self.user.username,
            'password': 'incorrect_password'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_server_keys_not_found(self):
        try:
            os.remove(os.path.join(settings.MIGASFREE_KEYS_DIR, settings.MIGASFREE_PUBLIC_KEY))
        except FileNotFoundError:
            pass

        response = self.client.post(self.url, {
            'username': self.user.username,
            'password': 'test'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(settings.MIGASFREE_PUBLIC_KEY, response.data)
        self.assertIn(settings.MIGASFREE_PACKAGER_PRI_KEY, response.data)


class TestProjectKeysView(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(
            name='testproject', platform=platform, pms='apt', architecture='amd64'
        )
        self.url = '/api/v1/public/keys/project/'

    def test_post_request_with_invalid_credentials(self):
        data = {
            'username': 'wrongusername',
            'password': 'wrongpassword',
            'project': 'testproject',
            'pms': 'apt',
            'platform': 'testplatform',
            'architecture': 'testarchitecture'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_request_with_valid_credentials(self):
        data = {
            'username': 'test',
            'password': 'test',
            'project': 'testproject',
            'pms': 'apt',
            'platform': 'testplatform',
            'architecture': 'testarchitecture'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_request_with_invalid_pms(self):
        data = {
            'username': 'test',
            'password': 'test',
            'project': 'testproject',
            'pms': 'wrongpms',
            'platform': 'testplatform',
            'architecture': 'testarchitecture'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_request_with_auto_register(self):
        settings.MIGASFREE_AUTOREGISTER = True
        data = {
            'username': 'test',
            'password': 'test',
            'project': 'testproject',
            'pms': 'apt',
            'platform': 'testplatform',
            'architecture': 'testarchitecture'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        settings.MIGASFREE_AUTOREGISTER = False

    def test_get_object_method(self):
        view = ProjectKeysView()
        view.user = self.user
        project = view.get_object(
            'testproject', 'testpms', 'testplatform', 'testarchitecture', '127.0.0.1'
        )
        self.assertEqual(project, self.project)

    def test_get_object_method_with_auto_register(self):
        settings.MIGASFREE_AUTOREGISTER = True
        view = ProjectKeysView()
        view.user = self.user
        project = view.get_object(
            'newproject', 'testpms', 'testplatform', 'testarchitecture', '127.0.0.1'
        )
        self.assertIsNotNone(project)
        settings.MIGASFREE_AUTOREGISTER = False


class TestRepositoriesKeysView(TestCase):
    def setUp(self):
        self.url = '/api/v1/public/keys/repositories/'

    def test_get_repository_key(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/plain')

    def test_invalid_request_method(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
