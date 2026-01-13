from datetime import date, datetime

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.client.models import Computer, Error
from migasfree.core.models import Platform, Project, UserProfile
from migasfree.stats.views.events import first_day_month, month_interval, month_year_iter


class StatsHelpersTestCase(APITestCase):
    def test_first_day_month(self):
        d = date(2023, 5, 15)
        self.assertEqual(first_day_month(d), date(2023, 5, 1))

    def test_month_year_iter(self):
        result = list(month_year_iter(11, 2023, 1, 2024))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], (2023, 11))
        self.assertEqual(result[1], (2023, 12))

    def test_month_interval(self):
        start, end = month_interval()
        if isinstance(end, datetime):
            end = end.date()
        self.assertTrue(start < end)

        start, end = month_interval('2023-01', '2023-03')
        if isinstance(end, datetime):
            end = end.date()
        self.assertEqual(start, date(2023, 1, 1))
        self.assertTrue(start <= end)


class StatsEventsApiTestCase(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create_user(username='admin', email='a@a.com', password='password')
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(user=self.user)

        self.platform = Platform.objects.create(name='Test Platform')

        self.project = Project.objects.create('Test Project', 'apt', 'x86_64', self.platform)

        self.computer = Computer.objects.create(name='computer1', uuid='uuid1', project=self.project)

        # ErrorManager.create(computer, project, description)
        self.error1 = Error.objects.create(self.computer, self.project, 'Error 1 details')

    def test_stats_errors_history(self):
        url = reverse('stats-errors-history')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('x_labels', response.data)
        self.assertIn('data', response.data)

    def test_stats_errors_by_day(self):
        url = reverse('stats-errors-by-day')
        response = self.client.get(url, {'computer_id': self.computer.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # to_heatmap returns list
        self.assertIsInstance(response.data, list)
