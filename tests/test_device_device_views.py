from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.client.models import Computer
from migasfree.core.models import Attribute, Platform, Project, Property, UserProfile
from migasfree.device.models import Connection, Device, Manufacturer, Model, Type


class TestDeviceViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        platform = Platform.objects.create(name='Linux')
        project = Project.objects.create(
            platform=platform, name='Vitalinux', pms='apt', architecture='amd64'
        )
        self.computer = Computer.objects.create(
            name='Test Computer', project=project, uuid='12345678-1234-1234-1234-123456789012'
        )

        property_att = Property.objects.create(
            prefix='CID', name='Computer ID', sort='basic'
        )
        self.attribute = Attribute.objects.create(value=str(self.computer.id), property_att=property_att)
        self.computer.sync_attributes.set([self.attribute.id])

        device_type = Type.objects.create(name='PRINTER')
        manufacturer = Manufacturer.objects.create(name='HP')
        self.connection = Connection.objects.create(name='USB', device_type=device_type)
        self.model = Model.objects.create(
            name='Test Model', manufacturer=manufacturer, device_type=device_type
        )
        self.model.connections.set([self.connection.id])
        self.device = Device.objects.create(
            name='Test Device', model=self.model, connection=self.connection
        )
        self.device.available_for_attributes.set([])

    def test_device_viewset_list(self):
        response = self.client.get(reverse('device-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], self.device.name)

    def test_device_viewset_detail(self):
        response = self.client.get(reverse('device-detail', kwargs={'pk': self.device.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.device.name)

    def test_device_viewset_create(self):
        data = {'name': 'New Device', 'model': self.model.id, 'connection': self.connection.id}
        response = self.client.post(reverse('device-list'), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Device.objects.count(), 2)

    def test_device_viewset_update(self):
        name = 'Updated device'
        data = {'name': name, 'model': self.model.id, 'connection': self.connection.id}
        response = self.client.put(reverse('device-detail', kwargs={'pk': self.device.pk}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.device.refresh_from_db()
        self.assertEqual(self.device.name, name)

    def test_device_viewset_destroy(self):
        response = self.client.delete(reverse('device-detail', kwargs={'pk': self.device.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Device.objects.count(), 0)

    def test_device_viewset_available(self):
        self.device.available_for_attributes.add(self.computer.sync_attributes.first())
        response = self.client.get(f"{reverse('device-list')}?cid={self.computer.pk}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], self.device.name)

    def test_device_viewset_available_with_query(self):
        self.device.available_for_attributes.add(self.computer.sync_attributes.first())
        response = self.client.get(f"{reverse('device-list')}?cid={self.computer.pk}&q={self.device.name}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], self.device.name)
