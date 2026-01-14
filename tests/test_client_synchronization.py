from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from django.test import TestCase
from django.utils.timezone import make_aware

from migasfree.client.models import Computer, Synchronization, User
from migasfree.core.models import Platform, Project


@pytest.mark.django_db
class SynchronizationModelTestCase(TestCase):
    def setUp(self):
        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(
            name='TestProject', pms='apt', architecture='amd64', platform=self.platform
        )
        self.user = User.objects.create(name='testuser', fullname='Test User')
        self.computer = Computer.objects.create(
            name='test-computer', project=self.project, uuid='12345678-1234-1234-1234-123456789012'
        )
        self.computer.sync_user = self.user
        self.computer.save()

    @patch('migasfree.client.models.synchronization.get_redis_connection')
    @patch('migasfree.core.models.Deployment.available_deployments')
    def test_synchronization_creation(self, mock_deployments, mock_redis):
        # Setup mocks
        mock_con = MagicMock()
        mock_redis.return_value = mock_con
        mock_con.sismember.return_value = False
        mock_deployments.return_value.values_list.return_value = []

        start_date = make_aware(datetime(2023, 1, 1, 10, 0, 0))
        sync = Synchronization.objects.create(computer=self.computer, start_date=start_date, pms_status_ok=True)

        self.assertEqual(sync.computer, self.computer)
        self.assertEqual(sync.project, self.project)
        self.assertEqual(sync.user, self.user)
        self.assertEqual(sync.start_date, start_date)
        self.assertTrue(sync.pms_status_ok)

        # Check signal triggered redis call
        mock_con.incr.assert_called()

        # Check computer sync_end_date updated
        self.computer.refresh_from_db()
        self.assertEqual(self.computer.sync_end_date, sync.created_at)

    @patch('migasfree.client.models.synchronization.get_redis_connection')
    @patch('migasfree.core.models.Deployment.available_deployments')
    def test_synchronization_save_updates_deployments_in_redis(self, mock_deployments, mock_redis):
        mock_con = MagicMock()
        mock_redis.return_value = mock_con
        mock_deployments.return_value.values_list.return_value = [101]

        Synchronization.objects.create(computer=self.computer, pms_status_ok=False)

        # Verify redis calls for deployments
        mock_con.srem.assert_any_call('migasfree:deployments:101:ok', self.computer.id)
        mock_con.srem.assert_any_call('migasfree:deployments:101:error', self.computer.id)
        mock_con.sadd.assert_any_call('migasfree:deployments:101:error', self.computer.id)

    @patch('migasfree.client.models.synchronization.get_redis_connection')
    def test_synchronization_pre_delete_cleanup_redis(self, mock_redis):
        mock_con = MagicMock()
        mock_redis.return_value = mock_con
        mock_con.sismember.return_value = True

        sync = Synchronization.objects.create(computer=self.computer)
        sync.delete()

        mock_con.decr.assert_called()
        mock_con.srem.assert_called()
