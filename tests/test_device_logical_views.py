from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.client.models import Computer
from migasfree.core.models import Attribute, Platform, Project, Property, UserProfile
from migasfree.device.models import Capability, Connection, Device, Logical, Manufacturer, Model, Type


class TestLogicalViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(platform=platform, name='Vitalinux', pms='apt', architecture='amd64')
        self.computer = Computer.objects.create(
            name='Test Computer', project=self.project, uuid='12345678-1234-1234-1234-123456789012'
        )

        property_att = Property.objects.create(prefix='CID', name='Computer ID', sort='basic')
        self.attribute = Attribute.objects.create(value=str(self.computer.id), property_att=property_att)
        self.computer.sync_attributes.set([self.attribute.id])

        self.device_type = Type.objects.create(name='PRINTER')
        self.manufacturer = Manufacturer.objects.create(name='HP')
        self.connection = Connection.objects.create(name='USB', device_type=self.device_type)
        self.capability = Capability.objects.create(name='Color')
        self.model = Model.objects.create(
            name='LaserJet Pro', manufacturer=self.manufacturer, device_type=self.device_type
        )
        self.model.connections.set([self.connection])

        self.device = Device.objects.create(name='Printer 1', model=self.model, connection=self.connection)
        self.device.available_for_attributes.set([self.attribute])

        self.logical = Logical.objects.create(device=self.device, capability=self.capability)

    def test_list_logicals(self):
        response = self.client.get(reverse('logical-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
        self.assertEqual(response.json()['results'][0]['id'], self.logical.id)

    def test_retrieve_logical(self):
        response = self.client.get(reverse('logical-detail', kwargs={'pk': self.logical.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['id'], self.logical.id)

    def test_create_logical(self):
        new_capability = Capability.objects.create(name='Duplex')
        data = {'device': self.device.id, 'capability': new_capability.id}
        response = self.client.post(reverse('logical-list'), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Logical.objects.count(), 2)

    def test_update_logical(self):
        new_capability = Capability.objects.create(name='Duplex')
        data = {'capability': new_capability.id}
        response = self.client.patch(reverse('logical-detail', kwargs={'pk': self.logical.pk}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_logical(self):
        response = self.client.delete(reverse('logical-detail', kwargs={'pk': self.logical.pk}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Logical.objects.filter(pk=self.logical.pk).exists())

    def test_available_action(self):
        response = self.client.get(reverse('logical-available'), {'cid': self.computer.pk})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)

    def test_available_action_with_query(self):
        response = self.client.get(reverse('logical-available'), {'cid': self.computer.pk, 'q': 'Printer'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)

    def test_available_action_with_device_filter(self):
        response = self.client.get(reverse('logical-available'), {'cid': self.computer.pk, 'did': self.device.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)
