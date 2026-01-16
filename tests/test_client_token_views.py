import unittest

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.client.models import (
    Computer,
    Error,
    Fault,
    FaultDefinition,
    Migration,
    Notification,
    PackageHistory,
    StatusLog,
    Synchronization,
    User,
)
from migasfree.core.models import Package, Platform, Project, UserProfile


class TestClientTokenViews(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(
            name='TestProject', pms='apt', architecture='amd64', platform=self.platform
        )
        self.computer = Computer.objects.create(
            name='test-computer', project=self.project, uuid='12345678-1234-1234-1234-123456789012'
        )
        self.sync_user = User.objects.create(name='testuser', fullname='Test User')

    def test_error_viewset(self):
        Error.objects.create(computer=self.computer, project=self.project, description='Test Error')
        url = reverse('error-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_fault_definition_viewset(self):
        FaultDefinition.objects.create(name='TestFault')
        url = reverse('faultdefinition-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_fault_viewset(self):
        fd = FaultDefinition.objects.create(name='TestFault')
        Fault.objects.create(computer=self.computer, definition=fd, result='Failed')
        url = reverse('fault-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_migration_viewset(self):
        Migration.objects.create(computer=self.computer, project=self.project)
        url = reverse('migration-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_notification_viewset(self):
        Notification.objects.create(message='Test Notification')
        url = reverse('notification-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_package_history_viewset(self):
        pkg = Package.objects.create(
            fullname='test-pkg_1.0_all.deb',
            name='test-pkg',
            version='1.0',
            architecture='all',
            project=self.project,
            store=None,
        )
        PackageHistory.objects.create(computer=self.computer, package=pkg)
        url = reverse('packagehistory-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_status_log_viewset(self):
        StatusLog.objects.create(computer=self.computer)
        url = reverse('statuslog-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # StatusLog.create() creates one log, and computer creation might trigger another or initial state?
        # Actually StatusLog.create just creates.
        self.assertGreaterEqual(len(response.data['results']), 1)

    @unittest.mock.patch('migasfree.client.models.synchronization.get_redis_connection')
    def test_synchronization_viewset(self, mock_redis):
        # Mock redis connection
        mock_con = unittest.mock.MagicMock()
        mock_redis.return_value = mock_con
        # Mock sismember to return False so it tries to add stats (and we don't care about the result for this test)
        mock_con.sismember.return_value = False

        self.computer.sync_user = self.sync_user
        self.computer.save()

        Synchronization.objects.create(computer=self.computer)
        url = reverse('synchronization-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_user_viewset(self):
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
