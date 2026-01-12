import random
from unittest.mock import patch

import redis
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.client.messages import add_computer_message
from migasfree.core.models import UserProfile


def generate_test_data():
    test_computer_id = random.randint(1, 100)
    test_project_id = random.randint(1, 100)
    test_project_name = f'Project {random.randint(1, 100)}'
    test_sync_user_id = random.randint(1, 100)
    test_sync_user_name = f'User {random.randint(1, 100)}'
    test_computer_name = f'Computer {random.randint(1, 100)}'
    test_computer_status = 'intended'
    test_computer_summary = f'Summary {random.randint(1, 100)}'
    test_msg = f'Proof message {random.randint(1, 100)}'

    class TestComputer:
        def __init__(self):
            self.id = test_computer_id
            self.name = test_computer_name
            self.status = test_computer_status
            self.project = Project(test_project_id, test_project_name)
            self.sync_user = SyncUser(test_sync_user_id, test_sync_user_name)

        def get_summary(self):
            return test_computer_summary

    class Project:
        def __init__(self, id, name):
            self.id = id
            self.name = name

    class SyncUser:
        def __init__(self, id, name):
            self.id = id
            self.name = name

    return TestComputer(), test_msg


class TestMessageViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=(settings.REDIS_DB + 1))

        test_computer, test_message = generate_test_data()
        add_computer_message(test_computer, test_message)

        test_computer, test_message = generate_test_data()
        add_computer_message(test_computer, test_message)

    def tearDown(self):
        self.redis_client.flushdb()

    def test_get_queryset(self):
        url = reverse('messages-list')
        response = self.client.get(url, {'project__id': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.json())

        response = self.client.get(url, {'computer__status__in': 'intended'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.data)
        self.assertIn('results', response.json())

        response = self.client.get(url, {'created_at__lt': '2022-01-01T03:45:21'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.json())

        response = self.client.get(url, {'search': 'something'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.json())

    def test_list(self):
        url = reverse('messages-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_destroy(self):
        url = reverse('messages-detail', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_export(self):
        response = self.client.get(reverse('messages-export'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get('Content-Disposition'), 'attachment; filename="messages.csv"')

    @patch('migasfree.client.messages.remove_computer_messages')
    def test_remove_computer_messages(self, mock_remove_computer_messages):
        mock_remove_computer_messages.return_value = None

        url = reverse('messages-detail', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_permission_denied(self):
        self.client.force_authenticate(user=None)

        url = reverse('messages-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MessageViewSetPaginationTest(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=(settings.REDIS_DB + 1))

        for _ in range(100):
            test_computer, test_message = generate_test_data()
            add_computer_message(test_computer, test_message)

    def tearDown(self):
        self.redis_client.flushdb()

    def test_pagination(self):
        url = reverse('messages-list')

        response = self.client.get(url, {'page_size': 20})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 20)
        self.assertIn('next', response.json())

        response = self.client.get(url, {'page_size': 20, 'page': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 20)
        self.assertIn('previous', response.json())

        response = self.client.get(url, {'page_size': 20, 'page': 6})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.json()['next'])
