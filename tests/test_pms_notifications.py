from unittest.mock import MagicMock, patch

import pytest
from celery import states
from django.test import TestCase

from migasfree.client.models import Notification
from migasfree.core.pms.tasks import create_repository_metadata, handle_postrun
from migasfree.core.tasks import process_notification_queue


@pytest.mark.django_db
class TestPMSNotifications(TestCase):
    @patch('redis.from_url')
    def test_notification_flow(self, mock_redis_from_url):
        # Mock Redis connection
        mock_con = MagicMock()
        mock_redis_from_url.return_value = mock_con

        # Setup mock behavior for rpop
        self.redis_messages = []

        def side_effect_lpush(queue, message):
            self.redis_messages.append(message)

        def side_effect_rpop(queue):
            if self.redis_messages:
                return self.redis_messages.pop(0).encode('utf-8')
            return None

        mock_con.lpush.side_effect = side_effect_lpush
        mock_con.rpop.side_effect = side_effect_rpop

        # 1. Simulate task logging - handle_postrun
        # Create a mock task object specifically mimicking what celery passes
        mock_sender = MagicMock()
        mock_sender.name = 'migasfree.core.pms.tasks.create_repository_metadata'

        retval = (0, 'Success output', 'deployment-slug', 'project-slug')
        kwargs = {'state': states.SUCCESS, 'retval': retval}

        # Call the signal handler
        handle_postrun(sender=create_repository_metadata, **kwargs)

        # Verify message was pushed to Redis
        mock_con.lpush.assert_called_once()
        self.assertEqual(len(self.redis_messages), 1)
        self.assertIn('Repository metadata for deployment', self.redis_messages[0])

        # 2. Simulate Consumer - process_notification_queue
        # We need to mock redis again inside the task if it creates a new connection
        # specific to the task execution context
        with (
            patch('migasfree.core.tasks.CELERY_BROKER_URL', 'redis://localhost:6379/0'),
            patch('redis.from_url', return_value=mock_con),
        ):
            process_notification_queue()

        # Verify notification was created in DB
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.first()
        self.assertIn('Repository metadata for deployment', notification.message)
