from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.core.models import Platform, Project, UserProfile
from migasfree.mgi.models import Build, Config, Flavour, Release


class MgiStatsApiTestCase(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create_user(username='admin', email='admin@test.com', password='password')
        self.user.is_superuser = True
        self.user.save()
        self.client.force_authenticate(user=self.user)

        self.platform = Platform.objects.create(name='Test Platform')
        self.project = Project.objects.create(
            name='Test Project',
            pms='apt',
            architecture='amd64',
            platform=self.platform,
        )

        self.config = Config.objects.create(
            project=self.project,
            template_id='debian-12-desktop',
            build_type='docker',
            base_os='debian',
            image_format='raw',
        )

        self.flavour = Flavour.objects.create(
            config=self.config,
            name='Desktop',
            enabled=True,
            user='tux',
        )

        self.release = Release.objects.create(
            config=self.config,
            name='v1.0',
        )

        now = timezone.now()
        # Build 1 (Success)
        self.build_success = Build.objects.create(
            release=self.release,
            flavour=self.flavour,
            status='completed',
            started_at=now - timedelta(minutes=10),
            finished_at=now,
            size=1024 * 1024,
        )

        # Build 2 (Failed)
        self.build_failed = Build.objects.create(
            release=self.release,
            flavour=self.flavour,
            status='failed',
            started_at=now - timedelta(minutes=5),
            finished_at=now,
            size=None,
        )

    def test_build_types_stats(self):
        url = reverse('stats-mgi-build-types')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('total', data)
        self.assertIn('inner', data)
        self.assertIn('outer', data)
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['inner'][0]['build_type'], 'docker')

    def test_build_status_stats(self):
        url = reverse('stats-mgi-build-status')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('total', data)
        self.assertIn('inner', data)
        self.assertIn('outer', data)
        self.assertEqual(data['total'], 2)

    def test_builds_by_month_stats(self):
        url = reverse('stats-mgi-builds-by-month')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('x_labels', data)
        self.assertIn('data', data)

    def test_build_metrics_stats(self):
        url = reverse('stats-mgi-build-metrics')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('avg_duration', data)
        self.assertIn('avg_size', data)
        self.assertIn('total_size', data)
        self.assertIn('total_completed', data)
        self.assertEqual(data['total_completed'], 1)  # only build_success is completed

    def test_flavours_stats(self):
        url = reverse('stats-mgi-flavours')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('total', data)
        self.assertIn('inner', data)
        self.assertIn('outer', data)
        self.assertEqual(data['total'], 1)
