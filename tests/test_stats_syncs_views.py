import redis

from django.conf import settings
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from migasfree.core.models import Project, Platform, UserProfile


class TestYearlySync(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(
            name='Vitalinux', platform=self.platform, pms='apt', architecture='amd64'
        )

        self.con = redis.Redis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB + 1
        )
        self.con.flushdb()

    def tearDown(self):
        self.con.flushdb()

    def test_yearly_sync_ok(self):
        self.con.set(f'migasfree:stats:{self.project.pk}:years:2022', '1')
        self.con.set('migasfree:stats:years:2022', '1')

        url = reverse('stats-syncs-yearly')
        params = {'begin': 2022, 'end': 2023, 'project_id': self.project.pk}
        response = self.client.get(url, data=params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_yearly_sync_no_project_id(self):
        self.con.set('migasfree:stats:years:2022', '1')

        url = reverse('stats-syncs-yearly')
        params = {'begin': 2022, 'end': 2023}
        response = self.client.get(url, data=params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_yearly_sync_invalid_project_id(self):
        self.con.set('migasfree:stats:years:2022', '1')

        url = reverse('stats-syncs-yearly')
        params = {'begin': 2022, 'end': 2023, 'project_id': 9999}
        response = self.client.get(url, data=params)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_yearly_sync_invalid_begin_end(self):
        self.con.set('migasfree:stats:years:2022', '1')

        url = reverse('stats-syncs-yearly')
        params = {'begin': 0, 'end': 2023}
        response = self.client.get(url, data=params)
        print(response.data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
