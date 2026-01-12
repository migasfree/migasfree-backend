from django.http import HttpRequest
from django.test import TestCase

from migasfree.api_v4.api import (
    get_properties,
    return_message,
    upload_computer_errors,
    upload_computer_faults,
    upload_computer_message,
)
from migasfree.client.models import Computer, Error, Fault, FaultDefinition
from migasfree.core.models import Attribute, Platform, Project, Property, UserProfile


class TestReturnMessage(TestCase):
    """Tests for return_message helper function."""

    def test_return_message_with_ok(self):
        result = return_message('test_cmd', {'status': 'ok'})
        self.assertEqual(result, {'test_cmd.return': {'status': 'ok'}})

    def test_return_message_with_error(self):
        result = return_message('upload_file', {'error': 'failed'})
        self.assertEqual(result, {'upload_file.return': {'error': 'failed'}})

    def test_return_message_with_string_data(self):
        result = return_message('simple_cmd', 'success')
        self.assertEqual(result, {'simple_cmd.return': 'success'})


class TestGetProperties(TestCase):
    """Tests for get_properties function."""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserProfile.objects.create(
            username='test', email='test@test.com', password='test', is_superuser=True
        )
        platform = Platform.objects.create(name='Linux')
        cls.project = Project.objects.create(name='TestProject', platform=platform, pms='apt', architecture='amd64')
        cls.computer = Computer.objects.create(
            uuid='12345678-1234-1234-1234-123456789999',
            name='TestComputer',
            project=cls.project,
        )
        # Create an enabled property
        Property.objects.create(
            prefix='TST', name='Test Property', enabled=True, kind='N', language=1, code="print 'test'"
        )

    def test_get_properties_returns_dict(self):
        request = HttpRequest()
        request.method = 'POST'

        result = get_properties(request, 'name', 'uuid', self.computer, {})

        self.assertIn('get_properties.return', result)
        self.assertIn('properties', result['get_properties.return'])
        self.assertIsInstance(result['get_properties.return']['properties'], list)


class TestUploadComputerMessage(TestCase):
    """Tests for upload_computer_message function."""

    @classmethod
    def setUpTestData(cls):
        platform = Platform.objects.create(name='Linux')
        cls.project = Project.objects.create(name='TestProject', platform=platform, pms='apt', architecture='amd64')
        cls.computer = Computer.objects.create(
            uuid='12345678-1234-1234-1234-123456789888',
            name='TestComputer',
            project=cls.project,
        )

    def test_upload_computer_message_no_computer(self):
        request = HttpRequest()
        result = upload_computer_message(request, 'name', 'uuid', None, {})

        self.assertIn('upload_computer_message.return', result)
        self.assertIn('errmfs', result['upload_computer_message.return'])

    def test_upload_computer_message_with_message(self):
        request = HttpRequest()
        data = {'upload_computer_message': 'Installing packages...'}
        result = upload_computer_message(request, 'name', 'uuid', self.computer, data)

        self.assertIn('upload_computer_message.return', result)


class TestUploadComputerErrors(TestCase):
    """Tests for upload_computer_errors function."""

    @classmethod
    def setUpTestData(cls):
        platform = Platform.objects.create(name='Linux')
        cls.project = Project.objects.create(name='TestProject', platform=platform, pms='apt', architecture='amd64')
        cls.computer = Computer.objects.create(
            uuid='12345678-1234-1234-1234-123456789777',
            name='TestComputer',
            project=cls.project,
        )

    def test_upload_computer_errors_creates_error(self):
        request = HttpRequest()
        data = {'upload_computer_errors': 'Connection failed to server'}
        initial_count = Error.objects.count()

        result = upload_computer_errors(request, 'name', 'uuid', self.computer, data)

        self.assertIn('upload_computer_errors.return', result)
        self.assertEqual(Error.objects.count(), initial_count + 1)


class TestUploadComputerFaults(TestCase):
    """Tests for upload_computer_faults function."""

    @classmethod
    def setUpTestData(cls):
        platform = Platform.objects.create(name='Linux')
        cls.project = Project.objects.create(name='TestProject', platform=platform, pms='apt', architecture='amd64')
        cls.computer = Computer.objects.create(
            uuid='12345678-1234-1234-1234-123456789666',
            name='TestComputer',
            project=cls.project,
        )
        property_att = Property.objects.create(prefix='SET', sort='basic', name='Attribute Set')
        Attribute.objects.create(description='All Systems', value='All Systems', property_att=property_att)
        cls.fault_def = FaultDefinition.objects.create(
            name='TestFault',
            language=1,
            code='exit 0',
            enabled=True,
        )

    def test_upload_computer_faults_with_no_result(self):
        """Fault with empty result should not create a Fault object."""
        request = HttpRequest()
        data = {'upload_computer_faults': {'faults': {'TestFault': ''}}}
        initial_count = Fault.objects.count()

        result = upload_computer_faults(request, 'name', 'uuid', self.computer, data)

        self.assertIn('upload_computer_faults.return', result)
        self.assertEqual(Fault.objects.count(), initial_count)

    def test_upload_computer_faults_with_result(self):
        """Fault with non-empty result should create a Fault object."""
        request = HttpRequest()
        data = {'upload_computer_faults': {'faults': {'TestFault': 'Disk space low: 95%'}}}
        initial_count = Fault.objects.count()

        result = upload_computer_faults(request, 'name', 'uuid', self.computer, data)

        self.assertIn('upload_computer_faults.return', result)
        self.assertEqual(Fault.objects.count(), initial_count + 1)

    def test_upload_computer_faults_unknown_definition(self):
        """Fault with unknown definition should be ignored."""
        request = HttpRequest()
        data = {'upload_computer_faults': {'faults': {'UnknownFault': 'Some error'}}}
        initial_count = Fault.objects.count()

        result = upload_computer_faults(request, 'name', 'uuid', self.computer, data)

        self.assertIn('upload_computer_faults.return', result)
        self.assertEqual(Fault.objects.count(), initial_count)
