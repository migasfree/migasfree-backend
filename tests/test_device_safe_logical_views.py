import unittest

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.client.models import Computer
from migasfree.core.models import Attribute, Platform, Project, Property
from migasfree.device.models import Capability, Connection, Device, Logical, Manufacturer, Model, Type


class TestSafeLogicalViewSet(APITestCase):
    def setUp(self):
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

    @unittest.mock.patch('migasfree.device.safe.SafeLogicalViewSet.get_claims')
    @unittest.mock.patch('migasfree.device.safe.SafeLogicalViewSet.create_response')
    def test_assign_logical(self, mock_create_response, mock_get_claims):
        mock_get_claims.return_value = {
            'cid': self.computer.pk,
            'id': self.logical.pk,
            'assigned': True
        }
        mock_create_response.side_effect = lambda x: {'msg': x}

        url = reverse('safe-logical-assign')
        response = self.client.post(url, {'msg': 'jwt'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.logical.attributes.filter(id=self.attribute.id).exists())

    @unittest.mock.patch('migasfree.device.safe.SafeLogicalViewSet.get_claims')
    @unittest.mock.patch('migasfree.device.safe.SafeLogicalViewSet.create_response')
    def test_unassign_logical(self, mock_create_response, mock_get_claims):
        # First assign it
        self.logical.attributes.add(self.attribute)

        mock_get_claims.return_value = {
            'cid': self.computer.pk,
            'id': self.logical.pk,
            'assigned': False
        }
        mock_create_response.side_effect = lambda x: {'msg': x}

        url = reverse('safe-logical-assign')
        response = self.client.post(url, {'msg': 'jwt'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.logical.attributes.filter(id=self.attribute.id).exists())

    @unittest.mock.patch('migasfree.device.safe.SafeLogicalViewSet.get_claims')
    @unittest.mock.patch('migasfree.device.safe.SafeLogicalViewSet.create_response')
    def test_assign_attributes_list(self, mock_create_response, mock_get_claims):
        mock_get_claims.return_value = {
            'cid': self.computer.pk,
            'id': self.logical.pk,
            'attributes': [self.attribute.id]
        }
        mock_create_response.side_effect = lambda x: {'msg': x}

        url = reverse('safe-logical-assign')
        response = self.client.post(url, {'msg': 'jwt'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.logical.attributes.filter(id=self.attribute.id).exists())

    @unittest.mock.patch('migasfree.device.safe.SafeLogicalViewSet.get_claims')
    @unittest.mock.patch('migasfree.device.safe.SafeLogicalViewSet.create_response')
    def test_available(self, mock_create_response, mock_get_claims):
        mock_get_claims.return_value = {
            'cid': self.computer.pk,
            'did': self.device.id
        }
        mock_create_response.side_effect = lambda x: x

        url = reverse('safe-logical-available')
        response = self.client.post(url, {'msg': 'jwt'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['id'], self.logical.id)

    @unittest.mock.patch('migasfree.device.safe.SafeLogicalViewSet.get_claims')
    @unittest.mock.patch('migasfree.device.safe.SafeLogicalViewSet.create_response')
    def test_available_assigned_but_not_available_attributes(self, mock_create_response, mock_get_claims):
        # Create a device not available for the computer's attributes
        device2 = Device.objects.create(name='Printer 2', model=self.model, connection=self.connection)
        # Create a logical device and assign it to the computer
        logical2 = Logical.objects.create(device=device2, capability=self.capability)
        logical2.attributes.set([self.attribute])

        mock_get_claims.return_value = {
            'cid': self.computer.pk,
            'did': device2.id
        }
        mock_create_response.side_effect = lambda x: x

        url = reverse('safe-logical-available')
        response = self.client.post(url, {'msg': 'jwt'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['id'], logical2.id)
