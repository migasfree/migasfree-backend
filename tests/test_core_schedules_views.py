from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.core.models import Attribute, Property, Schedule, ScheduleDelay, UserProfile


class TestScheduleViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.schedule = Schedule.objects.create(name='Default Schedule')

    def test_list_schedules(self):
        response = self.client.get(reverse('schedule-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
        self.assertGreaterEqual(response.json()['count'], 1)

    def test_retrieve_schedule(self):
        response = self.client.get(reverse('schedule-detail', kwargs={'pk': self.schedule.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], self.schedule.name)

    def test_create_schedule(self):
        data = {'name': 'Fast Schedule'}
        response = self.client.post(reverse('schedule-list'), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], data['name'])

    def test_update_schedule(self):
        data = {'name': 'Updated Schedule'}
        response = self.client.patch(reverse('schedule-detail', kwargs={'pk': self.schedule.pk}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], data['name'])

    def test_delete_schedule(self):
        schedule = Schedule.objects.create(name='ToDelete')
        response = self.client.delete(reverse('schedule-detail', kwargs={'pk': schedule.pk}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Schedule.objects.filter(pk=schedule.pk).exists())

    def test_search_schedule(self):
        response = self.client.get(reverse('schedule-list'), {'search': 'Default'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.json()['count'], 1)


class TestScheduleDelayViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.schedule = Schedule.objects.create(name='Default Schedule')
        self.property_att = Property.objects.create(name='Test Property', prefix='TST')
        self.attribute = Attribute.objects.create(property_att=self.property_att, value='value1')

        self.schedule_delay = ScheduleDelay.objects.create(schedule=self.schedule, delay=0, duration=1)
        self.schedule_delay.attributes.add(self.attribute)

    def test_list_schedule_delays(self):
        response = self.client.get(reverse('scheduledelay-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
        self.assertGreaterEqual(response.json()['count'], 1)

    def test_retrieve_schedule_delay(self):
        response = self.client.get(reverse('scheduledelay-detail', kwargs={'pk': self.schedule_delay.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['delay'], self.schedule_delay.delay)

    def test_create_schedule_delay(self):
        data = {
            'schedule': self.schedule.pk,
            'delay': 5,
            'duration': 2,
            'attributes': [self.attribute.pk],
        }
        response = self.client.post(reverse('scheduledelay-list'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['delay'], data['delay'])

    def test_update_schedule_delay(self):
        data = {'delay': 10}
        response = self.client.patch(reverse('scheduledelay-detail', kwargs={'pk': self.schedule_delay.pk}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['delay'], data['delay'])

    def test_delete_schedule_delay(self):
        schedule_delay = ScheduleDelay.objects.create(schedule=self.schedule, delay=99, duration=1)
        response = self.client.delete(reverse('scheduledelay-detail', kwargs={'pk': schedule_delay.pk}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ScheduleDelay.objects.filter(pk=schedule_delay.pk).exists())

    def test_filter_schedule_delay_by_schedule(self):
        response = self.client.get(reverse('scheduledelay-list'), {'schedule__id': self.schedule.pk})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.json()['count'], 1)
