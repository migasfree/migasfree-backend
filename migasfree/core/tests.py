# -*- coding: utf-8 -*-

# Copyright (c) 2015-2023 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2023 Alberto Gacías <alberto@migasfree.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Platform, UserProfile


class PlatformTestCase(APITestCase):
    def setUp(self):
        self.superuser = UserProfile.objects.create(
            username='admin', email='admin@localhost.com', password='admin',
            is_superuser=True, is_staff=True, is_active=True,
        )
        self.client.login(username='admin', password='admin')
        self.platform = Platform.objects.create(name='Linux')

    def test_get_platforms(self):
        url = reverse('platform-list')
        response = self.client.get(url)
        self.assertEqual(response.data['results'][0]['name'], 'Linux')

    def test_create_platform(self):
        url = reverse('platform-list')
        data = {'name': 'Windows'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_platform(self):
        url = reverse('platform-detail', args=[self.platform.id])
        data = {'name': 'GNU/Linux'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], data['name'])

    def test_delete_platform(self):
        url = reverse('platform-detail', args=[self.platform.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
