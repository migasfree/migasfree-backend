from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.core.models import Platform, Project, UserProfile
from migasfree.mgi.models import Build, Config, Flavour, Release


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

        url = '/api/v1/token/projects/templates/import/'
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

        url = '/api/v1/token/projects/templates/import/'
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

        url = '/api/v1/token/projects/templates/import/'
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

        url = '/api/v1/token/projects/templates/export/'
        payload = {'project_id': project.id}
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'status': 'exported'})

    def test_export_via_get_disallowed(self):
        url = '/api/v1/token/projects/templates/export/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_export_project_does_not_exist(self):
        url = '/api/v1/token/projects/templates/export/'
        payload = {'project_id': 99999}
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()['error'], 'Project with ID 99999 does not exist')

    @patch('requests.post')
    @patch('requests.get')
    def test_import_create_new_project_with_autoregister_success(self, mock_get, mock_post):
        # 1. Mock get response for template details with auto_register_computers = True
        mock_get_resp = mock_get.return_value
        mock_get_resp.status_code = status.HTTP_200_OK
        mock_get_resp.json.return_value = {
            'id': 'debian-13-autoreg',
            'base_os': 'debian',
            'platform': 'debian',
            'pms': 'apt',
            'architecture': 'amd64',
            'auto_register_computers': True,
            'dockerfile': 'FROM debian:13',
        }

        # 2. Mock post response for manager import trigger
        mock_post_resp = mock_post.return_value
        mock_post_resp.ok = True
        mock_post_resp.status_code = status.HTTP_200_OK
        mock_post_resp.json.return_value = {'status': 'imported'}

        self.assertFalse(Project.objects.filter(name='Autoreg Project').exists())

        url = '/api/v1/token/projects/templates/import/'
        payload = {
            'template_id': 'debian-13-autoreg',
            'project_name': 'Autoreg Project',
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Project.objects.filter(name='Autoreg Project').exists())
        project = Project.objects.get(name='Autoreg Project')
        self.assertEqual(project.platform.name, 'debian')
        self.assertEqual(project.pms, 'apt')
        self.assertEqual(project.architecture, 'amd64')
        self.assertTrue(project.auto_register_computers)

    @patch('requests.post')
    @patch('requests.get')
    def test_import_existing_project_with_autoregister_success(self, mock_get, mock_post):
        project = Project.objects.create(
            name='Existing Target Project',
            pms='yum',
            architecture='i386',
            platform=self.platform,
            auto_register_computers=False,
        )

        # 1. Mock get response for template details with auto_register_computers = True
        mock_get_resp = mock_get.return_value
        mock_get_resp.status_code = status.HTTP_200_OK
        mock_get_resp.json.return_value = {
            'id': 'debian-13-autoreg',
            'base_os': 'debian',
            'platform': 'debian',
            'pms': 'apt',
            'architecture': 'amd64',
            'auto_register_computers': True,
            'dockerfile': 'FROM debian:13',
        }

        # 2. Mock post response for manager import trigger
        mock_post_resp = mock_post.return_value
        mock_post_resp.ok = True
        mock_post_resp.status_code = status.HTTP_200_OK
        mock_post_resp.json.return_value = {'status': 'imported'}

        url = '/api/v1/token/projects/templates/import/'
        payload = {
            'template_id': 'debian-13-autoreg',
            'project_id': project.id,
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        project.refresh_from_db()
        self.assertEqual(project.pms, 'apt')
        self.assertEqual(project.architecture, 'amd64')
        self.assertTrue(project.auto_register_computers)


class TestMgiViewsScoping(APITestCase):
    def setUp(self):
        self.scoped_user = UserProfile.objects.create(
            username='scoped_user', email='scoped@test.com', password='test', is_superuser=False
        )
        self.client.force_authenticate(user=self.scoped_user)

        self.platform = Platform.objects.create(name='debian')

        # Create two projects
        self.project_1 = Project.objects.create(
            name='Project 1',
            pms='apt',
            architecture='amd64',
            platform=self.platform,
        )
        self.project_2 = Project.objects.create(
            name='Project 2',
            pms='apt',
            architecture='amd64',
            platform=self.platform,
        )

        # Create Configs
        self.config_1 = Config.objects.create(project=self.project_1, build_type='docker', image_format='raw')
        self.config_2 = Config.objects.create(project=self.project_2, build_type='docker', image_format='raw')

        # Create Flavours
        self.flavour_1 = Flavour.objects.create(config=self.config_1, name='flavour_1')
        self.flavour_2 = Flavour.objects.create(config=self.config_2, name='flavour_2')

        # Create Releases
        self.release_1 = Release.objects.create(config=self.config_1, name='release_1')
        self.release_2 = Release.objects.create(config=self.config_2, name='release_2')

        # Create Builds
        self.build_1 = Build.objects.create(release=self.release_1, flavour=self.flavour_1, status='success')
        self.build_2 = Build.objects.create(release=self.release_2, flavour=self.flavour_2, status='success')

    @patch.object(UserProfile, 'is_view_all', return_value=False)
    def test_mgi_views_scoping(self, mock_is_view_all):
        # We mock get_projects to only return project_1.id
        with patch.object(UserProfile, 'get_projects', return_value=[self.project_1.id]):
            # Test Config viewset
            response = self.client.get('/api/v1/token/mgi/config/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            results = response.json().get('results', response.json())
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['id'], self.config_1.id)

            # Test Flavour viewset
            response = self.client.get('/api/v1/token/mgi/flavour/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            results = response.json().get('results', response.json())
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['id'], self.flavour_1.id)

            # Test Release viewset
            response = self.client.get('/api/v1/token/mgi/release/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            results = response.json().get('results', response.json())
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['id'], self.release_1.id)

            # Test Build viewset
            response = self.client.get('/api/v1/token/mgi/build/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            results = response.json().get('results', response.json())
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['id'], self.build_1.id)

    @patch.object(UserProfile, 'is_view_all', return_value=True)
    def test_mgi_views_view_all(self, mock_is_view_all):
        # When user has is_view_all = True, they should see all records
        response = self.client.get('/api/v1/token/mgi/config/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json().get('results', response.json())
        self.assertEqual(len(results), 2)


class TestMgiViewsFilters(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='filter_user', email='filter@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.platform = Platform.objects.create(name='debian')
        self.project_1 = Project.objects.create(
            name='Project 1',
            pms='apt',
            architecture='amd64',
            platform=self.platform,
        )
        self.project_2 = Project.objects.create(
            name='Project 2',
            pms='apt',
            architecture='amd64',
            platform=self.platform,
        )

        self.config_1 = Config.objects.create(
            project=self.project_1,
            template_id='debian-12-desktop',
            build_type='docker',
            base_os='debian',
            image_format='raw',
        )
        self.config_2 = Config.objects.create(
            project=self.project_2,
            template_id='ubuntu-24.04-server',
            build_type='qemu_lnx',
            base_os='ubuntu',
            image_format='squashfs',
        )

        self.flavour_1 = Flavour.objects.create(
            config=self.config_1,
            name='Minimal',
            description='Minimal installation',
            hostname='minimal-host',
            enabled=True,
        )
        self.flavour_2 = Flavour.objects.create(
            config=self.config_2,
            name='Desktop',
            description='Desktop installation',
            hostname='desktop-host',
            enabled=False,
        )

        self.release_1 = Release.objects.create(config=self.config_1, name='v1.0', description='First release')
        self.release_2 = Release.objects.create(config=self.config_2, name='v2.0', description='Second release')

        self.build_1 = Build.objects.create(
            release=self.release_1, flavour=self.flavour_1, status='queued', task_id='task-123'
        )
        self.build_2 = Build.objects.create(
            release=self.release_2, flavour=self.flavour_2, status='completed', task_id='task-456'
        )

    def test_config_filters(self):
        # Filter by build_type
        response = self.client.get('/api/v1/token/mgi/config/', {'build_type': 'docker'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json().get('results', response.json())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.config_1.id)

        # Filter by image_format
        response = self.client.get('/api/v1/token/mgi/config/', {'image_format': 'squashfs'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json().get('results', response.json())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.config_2.id)

        # Search by template_id
        response = self.client.get('/api/v1/token/mgi/config/', {'search': 'ubuntu'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json().get('results', response.json())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.config_2.id)

    def test_flavour_filters(self):
        # Filter by enabled
        response = self.client.get('/api/v1/token/mgi/flavour/', {'enabled': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json().get('results', response.json())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.flavour_1.id)

        # Search by description
        response = self.client.get('/api/v1/token/mgi/flavour/', {'search': 'Desktop'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json().get('results', response.json())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.flavour_2.id)

    def test_release_filters(self):
        # Filter by name
        response = self.client.get('/api/v1/token/mgi/release/', {'name': 'v1.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json().get('results', response.json())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.release_1.id)

    def test_build_filters(self):
        # Filter by status
        response = self.client.get('/api/v1/token/mgi/build/', {'status': 'completed'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json().get('results', response.json())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.build_2.id)


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.db',
)
class TestMgiViewsPublish(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='publish_user', email='pub@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)
        self.platform = Platform.objects.create(name='debian')
        self.project = Project.objects.create(
            name='Project 1',
            pms='apt',
            architecture='amd64',
            platform=self.platform,
        )
        self.config = Config.objects.create(project=self.project, build_type='docker', image_format='raw')
        self.flavour = Flavour.objects.create(config=self.config, name='Minimal')
        self.release = Release.objects.create(config=self.config, name='v1.0')
        self.build = Build.objects.create(
            release=self.release, flavour=self.flavour, status='completed', task_id='task-123'
        )

    @patch('requests.post')
    def test_publish_success(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.ok = True
        mock_response.status_code = status.HTTP_200_OK
        mock_response.json.return_value = {'status': 'success'}

        url = f'/api/v1/token/mgi/build/{self.build.id}/publish/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.build.refresh_from_db()
        self.assertTrue(self.build.published)

    @patch('requests.post')
    def test_unpublish_success(self, mock_post):
        self.build.published = True
        self.build.save()

        mock_response = mock_post.return_value
        mock_response.ok = True
        mock_response.status_code = status.HTTP_200_OK
        mock_response.json.return_value = {'status': 'success'}

        url = f'/api/v1/token/mgi/build/{self.build.id}/unpublish/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.build.refresh_from_db()
        self.assertFalse(self.build.published)

    @patch('requests.delete')
    def test_destroy_success(self, mock_delete):
        mock_response = mock_delete.return_value
        mock_response.ok = True
        mock_response.status_code = status.HTTP_200_OK

        url = f'/api/v1/token/mgi/build/{self.build.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Build.objects.filter(id=self.build.id).exists())


class TestMgiSerializersStrField(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='str_user', email='str@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)
        self.platform = Platform.objects.create(name='debian')
        self.project = Project.objects.create(
            name='Project Str',
            pms='apt',
            architecture='amd64',
            platform=self.platform,
        )
        self.config = Config.objects.create(
            project=self.project, template_id='debian-12-desktop', build_type='docker', image_format='raw'
        )
        self.flavour = Flavour.objects.create(config=self.config, name='Minimal')
        self.release = Release.objects.create(config=self.config, name='v1.0')
        self.build = Build.objects.create(
            release=self.release, flavour=self.flavour, status='completed', task_id='task-123'
        )

    def test_flavour_serializer_includes_str(self):
        response = self.client.get(f'/api/v1/token/mgi/flavour/{self.flavour.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['__str__'], str(self.flavour))

    def test_release_serializer_includes_str(self):
        response = self.client.get(f'/api/v1/token/mgi/release/{self.release.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['__str__'], str(self.release))

    def test_build_serializer_includes_str(self):
        response = self.client.get(f'/api/v1/token/mgi/build/{self.build.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['__str__'], str(self.build))
