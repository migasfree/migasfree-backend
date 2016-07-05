# -*- coding: utf-8 -*-

# Copyright (c) 2015-2016 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2016 Alberto Gacías <alberto@migasfree.org>
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

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Platform


class PlatformTestCase(APITestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            'admin', 'admin@localhost.com', 'admin'
        )
        self.client.login(username='admin', password='admin')
        self.platform = Platform.objects.create(name='Linux')

    def test_get_platforms(self):
        url = reverse('platform-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.data[0]['name'], 'Linux')

    def test_create_platform(self):
        url = reverse('platform-list')
        data = {'name': 'Windows'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_platform(self):
        url = reverse('platform-detail', args=[self.platform.id])
        data = {'name': 'GNU/Linux'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_platform(self):
        url = reverse('platform-detail', args=[self.platform.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
