from django.http import HttpRequest
from django.test import TestCase

from migasfree.api_v4.api import get_computer, register_computer, upload_computer_info
from migasfree.client.models import Computer
from migasfree.core.models import Attribute, Platform, Project, Property, UserProfile
from migasfree.utils import uuid_change_format


class TestComputerAPI(TestCase):
    @classmethod
    def setUpTestData(cls):
        property_att = Property.objects.create(
            prefix='SET',
            sort='basic',
            name='Attribute Set',
            enabled=True,
            kind='N',
            language=1,
            code="print 'All Systems'"
        )
        Property.objects.create(
            prefix='HST',
            name='Hostname'
        )
        Attribute.objects.create(description='', value="All Systems", property_att=property_att)

        cls.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )

        platform = Platform.objects.create(name='Linux')
        project = Project.objects.create(name='Vitalinux', platform=platform, pms='apt', architecture='amd64')

        cls.computer1 = Computer.objects.create(
            uuid='12345678-1234-1234-1234-123456789012',
            name='Computer1',
            project=project,
        )
        cls.computer1.mac_address = '001122334455'
        cls.computer1.save()

        cls.computer2 = Computer.objects.create(
            uuid='01234567-0123-0123-0123-012345678901',
            name='Computer2',
            project=project,
        )
        cls.computer2.mac_address = '667788990011'
        cls.computer2.save()

        cls.computer3 = Computer.objects.create(
            uuid='00000000-9999-9999-9999-999999999999',
            name='Computer3',
            project=project,
        )
        cls.computer3.mac_address = '999999999999'
        cls.computer3.save()

    def test_get_computer_by_uuid(self):
        computer = get_computer(None, self.computer1.uuid)
        assert computer == self.computer1

    def test_get_computer_by_uuid_endian_format_changed(self):
        computer = get_computer(None, uuid_change_format(self.computer1.uuid))
        assert computer == self.computer1

    def test_get_computer_by_mac_address(self):
        computer = get_computer(None, self.computer3.uuid)
        assert computer == self.computer3

    def test_get_computer_by_name_compatibility_mode(self):
        computer = get_computer(self.computer1.name, self.computer1.uuid)
        assert computer == self.computer1

    def test_get_computer_by_name_compatibility_mode_client_lt_3(self):
        computer = get_computer(self.computer1.name, '01234567-0123-0123-0123-012345678901')
        assert computer == self.computer2

    def test_get_computer_not_found(self):
        computer = get_computer(None, '12345678-1234-1234-1234-123456789013')
        assert computer is None

    def test_get_computer_invalid_uuid(self):
        computer = get_computer(None, '12345678-1234-1234-1234-12345678901')
        assert computer is None

    def test_get_computer_invalid_name_and_uuid(self):
        computer = get_computer('Invald name', '12345678-1234-1234-1234-12345678901')
        assert computer is None

    def test_upload_computer_info_ok(self):
        request = HttpRequest()
        request.method = 'POST'

        data = {
            'upload_computer_info': {
                'computer': {
                    'hostname': 'localhost',
                    'ip': '127.0.0.1',
                    'platform': 'Windows',
                    'project': 'Windows 10',
                    'user': 'tux',
                    'user_fullname': 'tux'
                },
                'attributes': {
                    'HST': 'localhost'
                }
            }
        }

        response = upload_computer_info(
            request, 'localhost', '12345678-1234-1234-1234-12345678901', self.computer1, data
        )
        response = response['upload_computer_info.return']

        assert isinstance(response, dict)
        assert 'faultsdef' in response
        assert 'repositories' in response
        assert 'packages' in response
        assert 'devices' in response
        assert 'base' in response
        assert 'hardware_capture' in response

    def test_resgister_computer(self):
        request = HttpRequest()
        request.method = 'POST'

        uuid = '12345678-1234-1234-1234-123456789015'
        platform_name = 'Apple'
        project_name = 'Leopard'
        computer_name = 'number5'
        data = {
            'username': self.user.username,
            'password': self.user.password,
            'platform': platform_name,
            'project': project_name,
            'pms': 'homebrew',
            'fqdn': f'{computer_name}.domain.com',
            'name': computer_name,
            'uuid': uuid,
            'ip': '192.168.1.22',
        }

        register_computer(request, computer_name, uuid, None, data)

        self.assertEqual(Platform.objects.filter(name=platform_name).exists(), True)
        self.assertEqual(Project.objects.filter(name=project_name).exists(), True)
        self.assertEqual(Computer.objects.filter(name=computer_name).exists(), True)
