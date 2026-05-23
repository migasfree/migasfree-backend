from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.core.models import Platform, Project, UserProfile


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.db',
)
class TestProjectTemplatesView(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

    @patch('requests.get')
    def test_get_templates_success(self, mock_get):
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

        url = reverse('project-templates')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), mock_response.json.return_value)
        mock_get.assert_called_once_with(
            'http://manager:8080/manager/v1/internal/mgi/projects/templates', headers={}, timeout=15.0
        )

    @patch('requests.get')
    def test_get_templates_failure(self, mock_get):
        # Mock failed manager response
        mock_response = mock_get.return_value
        mock_response.ok = False
        mock_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        mock_response.text = 'Internal error on manager'

        url = reverse('project-templates')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.json()['error'], 'Manager responded with HTTP 500')
        self.assertEqual(response.json()['details'], 'Internal error on manager')

    @patch('requests.get')
    def test_get_templates_exception(self, mock_get):
        # Mock exception connecting to manager
        mock_get.side_effect = Exception('Connection refused')

        url = reverse('project-templates')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('Could not connect to manager: Connection refused', response.json()['error'])

    def test_get_templates_unauthorized(self):
        self.client.force_authenticate(user=None)
        url = reverse('project-templates')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.db',
)
class TestProjectTemplateImportList(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test_import', email='test_import@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)
        self.platform = Platform.objects.create(name='debian')

    @patch('requests.post')
    @patch('requests.get')
    def test_import_create_new_project_success(self, mock_get, mock_post):
        # 1. Mock get response for template details
        mock_get_resp = mock_get.return_value
        mock_get_resp.status_code = status.HTTP_200_OK
        mock_get_resp.json.return_value = {
            'id': 'debian-13',
            'base_os': 'debian',
            'platform': 'debian',
            'pms': 'apt',
            'architecture': 'amd64',
            'dockerfile': 'FROM debian:13',
        }

        # 2. Mock post response for manager import trigger
        mock_post_resp = mock_post.return_value
        mock_post_resp.ok = True
        mock_post_resp.status_code = status.HTTP_200_OK
        mock_post_resp.json.return_value = {'status': 'imported'}

        # Ensure project does not exist
        self.assertFalse(Project.objects.filter(name='New Brand Project').exists())

        url = '/api/v1/token/projects/template-import/'
        payload = {
            'template_id': 'debian-13',
            'project_name': 'New Brand Project',
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('config', response.json())
        self.assertTrue(response.json()['config_created'])

        # Verify project was created with metadata from template
        self.assertTrue(Project.objects.filter(name='New Brand Project').exists())
        project = Project.objects.get(name='New Brand Project')
        self.assertEqual(project.platform.name, 'debian')
        self.assertEqual(project.pms, 'apt')
        self.assertEqual(project.architecture, 'amd64')

    def test_import_create_new_project_already_exists(self):
        # Create project with this name
        Project.objects.create(
            name='Existing Project',
            pms='apt',
            architecture='amd64',
            platform=self.platform,
            auto_register_computers=False,
        )

        url = '/api/v1/token/projects/template-import/'
        payload = {
            'template_id': 'debian-13',
            'project_name': 'Existing Project',
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['error'], "A project with name 'Existing Project' already exists")

    @patch('requests.post')
    @patch('requests.get')
    def test_import_existing_project_success(self, mock_get, mock_post):
        # Create existing project with different PMS and arch
        project = Project.objects.create(
            name='Target Project',
            pms='yum',
            architecture='i386',
            platform=self.platform,
            auto_register_computers=False,
        )

        # 1. Mock get response for template details
        mock_get_resp = mock_get.return_value
        mock_get_resp.status_code = status.HTTP_200_OK
        mock_get_resp.json.return_value = {
            'id': 'debian-13',
            'base_os': 'debian',
            'platform': 'debian',
            'pms': 'apt',
            'architecture': 'amd64',
            'dockerfile': 'FROM debian:13',
        }

        # 2. Mock post response for manager import trigger
        mock_post_resp = mock_post.return_value
        mock_post_resp.ok = True
        mock_post_resp.status_code = status.HTTP_200_OK
        mock_post_resp.json.return_value = {'status': 'imported'}

        url = '/api/v1/token/projects/template-import/'
        payload = {
            'template_id': 'debian-13',
            'project_id': project.id,
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Refresh project and verify PMS and architecture were updated
        project.refresh_from_db()
        self.assertEqual(project.pms, 'apt')
        self.assertEqual(project.architecture, 'amd64')

    @patch('requests.get')
    def test_export_success_via_post(self, mock_get):
        project = Project.objects.create(
            name='Export Proj',
            pms='apt',
            architecture='amd64',
            platform=self.platform,
            auto_register_computers=False,
        )

        mock_resp = mock_get.return_value
        mock_resp.ok = True
        mock_resp.status_code = status.HTTP_200_OK
        mock_resp.content = b'{"status": "exported"}'

        url = '/api/v1/token/projects/template-export/'
        payload = {'project_id': project.id}
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'status': 'exported'})

    def test_export_via_get_disallowed(self):
        url = '/api/v1/token/projects/template-export/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_export_project_does_not_exist(self):
        url = '/api/v1/token/projects/template-export/'
        payload = {'project_id': 99999}
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()['error'], 'Project with ID 99999 does not exist')
