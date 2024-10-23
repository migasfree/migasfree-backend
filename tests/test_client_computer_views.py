import uuid

from rest_framework import status
from rest_framework.test import APITestCase
from django.conf import settings
from django.urls import reverse

from migasfree.client.models import Computer, Fault, FaultDefinition
from migasfree.core.models import UserProfile, Platform, Project
from migasfree.hardware.models import Node


class TestHardwareComputerViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(
            name='Vitalinux', pms='apt', architecture='amd64', platform=self.platform
        )
        self.computer = Computer.objects.create(
            name='PCXXXXX', project=self.project, uuid=str(uuid.uuid4())
        )
        self.computer2 = Computer.objects.create(
            name='PCXXXX1', project=self.project, uuid=str(uuid.uuid4())
        )
        self.node1 = Node.objects.create(
            data={
                'computer': self.computer,
                'level': 1,
                'name': 'name1',
                'class_name': 'cl1',
            }
        )
        self.node2 = Node.objects.create(
            data={
                'computer': self.computer,
                'level': 2,
                'name': 'name2',
                'class_name': 'cl2',
                'parent': self.node1,
            }
        )
        self.fault_definition = FaultDefinition.objects.create(name='One', enabled=True)
        self.fault1 = Fault.objects.create(
            computer=self.computer, definition=self.fault_definition, result='Fault 1'
        )
        self.fault2 = Fault.objects.create(
            computer=self.computer, definition=self.fault_definition, result='Fault 2'
        )
        self.fault2.checked_ok()

    def test_hardware_action(self):
        url = reverse('computer-hardware', kwargs={'pk': self.computer.pk})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 2

    def test_hardware_action_with_invalid_computer(self):
        url = reverse('computer-hardware', kwargs={'pk': 9999999})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_label_method_returns_200_status_code(self):
        url = reverse('computer-label', kwargs={'pk': self.computer.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_label_method_returns_expected_response(self):
        url = reverse('computer-label', kwargs={'pk': self.computer.pk})
        response = self.client.get(url)
        expected_response = {
            'uuid': self.computer.uuid,
            'name': self.computer.name,
            'search': str(self.computer),
            'helpdesk': settings.MIGASFREE_HELP_DESK
        }
        self.assertEqual(response.json(), expected_response)

    def test_label_method_returns_404_status_code_if_computer_does_not_exist(self):
        url = reverse('computer-label', kwargs={'pk': 99999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_status_change(self):
        url = reverse('computer-status', kwargs={'pk': self.computer.pk})
        data = {'status': 'reserved'}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'reserved')
    def test_status_invalid(self):
        url = reverse('computer-status', kwargs={'pk': self.computer.pk})
        data = {'status': 'invalid'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_status_not_found(self):
        url = reverse('computer-status', kwargs={'pk': 999999})
        data = {'status': 'available'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_faults(self):
        url = reverse('computer-faults', kwargs={'pk': self.computer.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unchecked'], 1)
        self.assertEqual(response.data['total'], 2)

    def test_get_faults_with_no_faults(self):
        url = reverse('computer-faults', kwargs={'pk': self.computer.pk})
        Fault.objects.all().delete()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unchecked'], 0)
        self.assertEqual(response.data['total'], 0)

    def test_get_faults_with_multiple_computers(self):
        Fault.objects.create(
            computer=self.computer2, result='Other fault 1', definition=self.fault_definition
        )
        url = reverse('computer-faults', kwargs={'pk': self.computer.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unchecked'], 1)
        self.assertEqual(response.data['total'], 2)
