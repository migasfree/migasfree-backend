from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.core.models import Platform, Project, Store, UserProfile


class TestPlatformViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.platform = Platform.objects.create(name='Linux')

    def test_list_platforms(self):
        response = self.client.get(reverse('platform-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
        self.assertGreaterEqual(response.json()['count'], 1)

    def test_retrieve_platform(self):
        response = self.client.get(reverse('platform-detail', kwargs={'pk': self.platform.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], self.platform.name)

    def test_create_platform(self):
        data = {'name': 'Windows'}
        response = self.client.post(reverse('platform-list'), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], data['name'])

    def test_update_platform(self):
        data = {'name': 'macOS'}
        response = self.client.patch(reverse('platform-detail', kwargs={'pk': self.platform.pk}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], data['name'])

    def test_delete_platform(self):
        platform = Platform.objects.create(name='ToDelete')
        response = self.client.delete(reverse('platform-detail', kwargs={'pk': platform.pk}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Platform.objects.filter(pk=platform.pk).exists())

    def test_search_platform(self):
        response = self.client.get(reverse('platform-list'), {'search': 'Linux'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.json()['count'], 1)


class TestProjectViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(name='Vitalinux', pms='apt', architecture='amd64', platform=self.platform)

    def test_list_projects(self):
        response = self.client.get(reverse('project-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
        self.assertGreaterEqual(response.json()['count'], 1)

    def test_retrieve_project(self):
        response = self.client.get(reverse('project-detail', kwargs={'pk': self.project.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], self.project.name)

    def test_create_project(self):
        data = {
            'name': 'Ubuntu',
            'pms': 'apt',
            'architecture': 'amd64',
            'platform': self.platform.pk,
        }
        response = self.client.post(reverse('project-list'), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], data['name'])

    def test_create_duplicate_slug_project(self):
        # Try to create a project with same slug
        data = {
            'name': 'Vitalinux',  # Same name as existing
            'pms': 'apt',
            'architecture': 'amd64',
            'platform': self.platform.pk,
        }
        response = self.client.post(reverse('project-list'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_project(self):
        data = {'name': 'Vitalinux-EDU'}
        response = self.client.patch(reverse('project-detail', kwargs={'pk': self.project.pk}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], data['name'])

    def test_search_project(self):
        response = self.client.get(reverse('project-list'), {'search': 'Vital'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.json()['count'], 1)


class TestStoreViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(name='Vitalinux', pms='apt', architecture='amd64', platform=self.platform)
        self.store = Store.objects.create(name='Main Store', project=self.project)

    def test_list_stores(self):
        response = self.client.get(reverse('store-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
        self.assertGreaterEqual(response.json()['count'], 1)

    def test_retrieve_store(self):
        response = self.client.get(reverse('store-detail', kwargs={'pk': self.store.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], self.store.name)

    def test_create_store(self):
        data = {
            'name': 'Custom Store',
            'project': self.project.pk,
        }
        response = self.client.post(reverse('store-list'), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], data['name'])

    def test_update_store(self):
        data = {'name': 'Updated Store'}
        response = self.client.patch(reverse('store-detail', kwargs={'pk': self.store.pk}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], data['name'])

    def test_delete_store(self):
        store = Store.objects.create(name='ToDelete', project=self.project)
        response = self.client.delete(reverse('store-detail', kwargs={'pk': store.pk}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Store.objects.filter(pk=store.pk).exists())

    def test_search_store(self):
        response = self.client.get(reverse('store-list'), {'search': 'Main'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.json()['count'], 1)

    def test_filter_store_by_project(self):
        response = self.client.get(reverse('store-list'), {'project__id': self.project.pk})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.json()['count'], 1)
