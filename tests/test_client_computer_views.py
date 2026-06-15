import unittest
import uuid

from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.client.models import Computer, Fault, FaultDefinition
from migasfree.core.models import Attribute, Platform, Project, Property, ServerAttribute, UserProfile
from migasfree.hardware.models import Node


class TestHardwareComputerViewSet(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(name='Vitalinux', pms='apt', architecture='amd64', platform=self.platform)
        self.computer = Computer.objects.create(name='PCXXXXX', project=self.project, uuid=str(uuid.uuid4()))
        self.computer2 = Computer.objects.create(name='PCXXXX1', project=self.project, uuid=str(uuid.uuid4()))
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
        self.fault1 = Fault.objects.create(computer=self.computer, definition=self.fault_definition, result='Fault 1')
        self.fault2 = Fault.objects.create(computer=self.computer, definition=self.fault_definition, result='Fault 2')
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
            'helpdesk': settings.MIGASFREE_HELP_DESK,
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
        Fault.objects.create(computer=self.computer2, result='Other fault 1', definition=self.fault_definition)
        url = reverse('computer-faults', kwargs={'pk': self.computer.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unchecked'], 1)
        self.assertEqual(response.data['total'], 2)

    @unittest.mock.patch('migasfree.client.views.safe.computer.SafeComputerViewSet.get_claims')
    @unittest.mock.patch('migasfree.client.views.safe.computer.SafeComputerViewSet.create_response')
    def test_safe_info_endpoint(self, mock_create_response, mock_get_claims):
        mock_get_claims.return_value = {'id': self.computer.pk}
        mock_create_response.side_effect = lambda x: {'msg': x}

        # Safe router has basename 'computers', so info action route name is 'computers-info'
        url = reverse('computers-info')
        data = {'msg': 'encrypted_jwt', 'project': self.project.name}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res_data = response.json()
        self.assertEqual(res_data['msg']['uuid'], self.computer.uuid)
        self.assertEqual(res_data['msg']['name'], self.computer.name)
        self.assertIn('product_system', res_data['msg'])

    @unittest.mock.patch('migasfree.client.views.safe.computer.SafeComputerViewSet.get_claims')
    @unittest.mock.patch('migasfree.client.views.safe.computer.SafeComputerViewSet.create_response')
    def test_safe_cid_attribute_endpoint(self, mock_create_response, mock_get_claims):
        cid_prop = Property.objects.create(prefix='CID', name='COMPUTER ID', enabled=True, kind='N', sort='client')
        cid_attr = Attribute.objects.create(
            property_att=cid_prop, value=str(self.computer.pk), description=self.computer.name
        )

        mock_get_claims.return_value = {'id': self.computer.pk}
        mock_create_response.side_effect = lambda x: {'msg': x}

        url = reverse('computers-cid-attribute')
        data = {'msg': 'encrypted_jwt', 'project': self.project.name}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res_data = response.json()

        self.assertEqual(res_data['msg']['count'], 1)
        self.assertEqual(len(res_data['msg']['results']), 1)
        self.assertEqual(res_data['msg']['results'][0]['id'], cid_attr.pk)
        self.assertEqual(res_data['msg']['results'][0]['value'], str(self.computer.pk))
        self.assertEqual(res_data['msg']['results'][0]['description'], self.computer.name)

    @unittest.mock.patch('migasfree.client.views.safe.computer.SafeComputerViewSet.get_claims')
    @unittest.mock.patch('migasfree.client.views.safe.computer.SafeComputerViewSet.create_response')
    def test_safe_assigned_attributes_endpoint(self, mock_create_response, mock_get_claims):
        org_prop = Property.objects.create(prefix='ORG', name='ORGANIZATION', enabled=True, kind='N', sort='client')
        org_attr = Attribute.objects.create(property_att=org_prop, value='HEADQUARTERS')

        self.computer.sync_attributes.add(org_attr)

        mock_get_claims.return_value = {'id': self.computer.pk}
        mock_create_response.side_effect = lambda x: {'msg': x}

        url = reverse('computers-assigned-attributes')
        data = {'msg': 'encrypted_jwt', 'project': self.project.name}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res_data = response.json()

        self.assertEqual(res_data['msg']['count'], 1)
        self.assertEqual(len(res_data['msg']['results']), 1)
        self.assertEqual(res_data['msg']['results'][0]['id'], org_attr.pk)
        self.assertEqual(res_data['msg']['results'][0]['value'], 'HEADQUARTERS')

    @unittest.mock.patch('requests.get')
    def test_remote_access_agent_online(self, mock_get):
        """Test remote-access endpoint when agent is online in the Manager."""
        mock_response = unittest.mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': self.computer.pk,
            'name': 'PC-TEST',
            'services': ['ssh', 'vnc'],
            'relay': 'wss://relay.example.com/tunnel',
        }
        mock_get.return_value = mock_response

        url = reverse('computer-remote-access', kwargs={'pk': self.computer.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res_data = response.json()
        self.assertEqual(res_data['status'], 'online')
        self.assertEqual(res_data['id'], self.computer.pk)
        self.assertEqual(res_data['services'], ['ssh', 'vnc'])
        self.assertEqual(res_data['relay'], 'wss://relay.example.com/tunnel')
        mock_get.assert_called_once()

    @unittest.mock.patch('requests.get')
    def test_remote_access_agent_offline(self, mock_get):
        """Test remote-access endpoint when agent is offline in the Manager (404)."""
        mock_response = unittest.mock.MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        url = reverse('computer-remote-access', kwargs={'pk': self.computer.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res_data = response.json()
        self.assertEqual(res_data['status'], 'offline')
        self.assertNotIn('services', res_data)
        mock_get.assert_called_once()

    @unittest.mock.patch('requests.get')
    def test_remote_access_manager_error(self, mock_get):
        """Test remote-access endpoint when Manager is down or returns error."""
        import requests

        mock_get.side_effect = requests.RequestException('Connection refused')

        url = reverse('computer-remote-access', kwargs={'pk': self.computer.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        res_data = response.json()
        self.assertEqual(res_data['status'], 'unknown')
        self.assertIn('error', res_data)
        mock_get.assert_called_once()

    @unittest.mock.patch('migasfree.client.views.safe.computer.SafeComputerViewSet.get_claims')
    @unittest.mock.patch('migasfree.client.views.safe.computer.SafeComputerViewSet.create_response')
    def test_safe_tags_valid_list(self, mock_create_response, mock_get_claims):
        tag_prop = Property.objects.create(prefix='LOC', name='Location', enabled=True, kind='N', sort='server')
        ServerAttribute.objects.create(property_att=tag_prop, value='office1')
        Attribute.objects.get_or_create(pk=1, defaults={'property_att': tag_prop, 'value': 'All Systems'})

        mock_get_claims.return_value = {'id': self.computer.pk, 'tags': ['LOC-office1']}
        mock_create_response.side_effect = lambda x: {'msg': x}

        url = reverse('computers-tags')
        data = {'msg': 'encrypted_jwt', 'project': self.project.name}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('LOC-office1', [str(t) for t in self.computer.tags.all()])

    @unittest.mock.patch('migasfree.client.views.safe.computer.SafeComputerViewSet.get_claims')
    @unittest.mock.patch('migasfree.client.views.safe.computer.SafeComputerViewSet.create_response')
    def test_safe_tags_empty_list(self, mock_create_response, mock_get_claims):
        tag_prop = Property.objects.create(prefix='LOC', name='Location', enabled=True, kind='N', sort='server')
        tag_attr = ServerAttribute.objects.create(property_att=tag_prop, value='office1')
        self.computer.tags.add(tag_attr)
        self.assertEqual(self.computer.tags.count(), 1)

        mock_get_claims.return_value = {'id': self.computer.pk, 'tags': []}
        mock_create_response.side_effect = lambda x: {'msg': x}

        url = reverse('computers-tags')
        data = {'msg': 'encrypted_jwt', 'project': self.project.name}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.computer.tags.count(), 0)

    @unittest.mock.patch('migasfree.client.views.safe.computer.SafeComputerViewSet.get_claims')
    @unittest.mock.patch('migasfree.client.views.safe.computer.SafeComputerViewSet.create_response')
    def test_safe_tags_invalid_list(self, mock_create_response, mock_get_claims):
        mock_get_claims.return_value = {'id': self.computer.pk, 'tags': ['INVALID-tag']}
        mock_create_response.side_effect = lambda x: {'msg': x}

        url = reverse('computers-tags')
        data = {'msg': 'encrypted_jwt', 'project': self.project.name}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
