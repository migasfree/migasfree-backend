from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.client.models import Computer
from migasfree.core.models import Platform, Project, UserProfile
from migasfree.hardware.models import Capability, Configuration, LogicalName, Node


class HardwareApiTestCase(APITestCase):
    def setUp(self):
        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(
            name='TestProject', pms='apt', architecture='x86_64', platform=self.platform
        )
        # Create UserProfile directly instead of User
        self.user_profile = UserProfile.objects.create_superuser(
            username='admin', password='password', email='admin@test.com'
        )
        self.client.force_authenticate(user=self.user_profile)

        self.computer = Computer.objects.create(
            project=self.project, name='test-computer', uuid='12345678-1234-1234-1234-123456789012'
        )

        self.node = Node.objects.create(
            {
                'computer': self.computer,
                'level': 0,
                'width': 64,
                'name': 'test-node',
                'class_name': 'system',
                'enabled': True,
                'description': 'Test Description',
                'vendor': 'Test Vendor',
                'product': 'Test Product',
            }
        )

    def test_list_hardware(self):
        url = reverse('node-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'test-node')

    def test_retrieve_hardware_info(self):
        Capability.objects.create(node=self.node, name='cap1', description='desc1')
        LogicalName.objects.create(node=self.node, name='log1')
        Configuration.objects.create(node=self.node, name='conf1', value='val1')

        url = reverse('node-info', kwargs={'pk': self.node.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Detailed name in Response is node.__str__() which is product or name
        self.assertEqual(response.data['name'], 'Test Product')
        self.assertEqual(len(response.data['capability']), 1)
        self.assertEqual(response.data['capability'][0]['name'], 'cap1')
        self.assertEqual(len(response.data['logical_name']), 1)
        self.assertEqual(response.data['logical_name'][0]['name'], 'log1')
        self.assertEqual(len(response.data['configuration']), 1)
        self.assertEqual(response.data['configuration'][0]['name'], 'conf1')
