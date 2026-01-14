from django.test import TestCase

from migasfree.client.models import Computer
from migasfree.core.models import Platform, Project
from migasfree.hardware.models import Configuration, Node


class NodeModelTestCase(TestCase):
    def setUp(self):
        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(
            name='TestProject', pms='apt', architecture='x86_64', platform=self.platform
        )
        self.computer = Computer.objects.create(
            project=self.project, name='test-computer', uuid='12345678-1234-1234-1234-123456789012'
        )

    def test_node_creation(self):
        node = Node.objects.create(
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
        self.assertEqual(node.computer, self.computer)
        self.assertEqual(node.name, 'test-node')
        self.assertEqual(str(node), 'Test Product')

    def test_get_product(self):
        # Test virtual machine detection
        node_vbox = Node.objects.create(
            {
                'computer': self.computer,
                'level': 0,
                'vendor': 'innotek GmbH',
                'product': 'VirtualBox',
                'name': 'node1',
                'class_name': 'system',
            }
        )
        self.assertEqual(node_vbox.get_product(), 'virtualbox')

        # Test normal product
        node_normal = Node.objects.create(
            {
                'computer': self.computer,
                'level': 0,
                'vendor': 'Intel',
                'product': 'Core i7',
                'name': 'node2',
                'class_name': 'processor',
            }
        )
        self.assertEqual(node_normal.get_product(), 'Core i7')

    def test_get_is_vm(self):
        # Create a VM node
        Node.objects.create(
            {
                'computer': self.computer,
                'level': 0,
                'vendor': 'QEMU',
                'product': 'Standard PC',
                'name': 'node1',
                'class_name': 'system',
                'parent': None,
            }
        )
        self.assertTrue(Node.get_is_vm(self.computer.id))

        # Create another computer and a non-VM node
        computer2 = Computer.objects.create(
            project=self.project, name='test-computer-2', uuid='87654321-4321-4321-4321-210987654321'
        )
        Node.objects.create(
            {
                'computer': computer2,
                'level': 0,
                'vendor': 'Dell Inc.',
                'product': 'OptiPlex 7040',
                'name': 'node2',
                'class_name': 'system',
                'parent': None,
            }
        )
        self.assertFalse(Node.get_is_vm(computer2.id))

    def test_get_is_laptop(self):
        node = Node.objects.create({'computer': self.computer, 'level': 0, 'class_name': 'system', 'name': 'computer'})
        Configuration.objects.create(node=node, name='chassis', value='laptop')
        self.assertTrue(Node.get_is_laptop(self.computer.id))

    def test_get_ram(self):
        Node.objects.create(
            {
                'computer': self.computer,
                'level': 1,
                'name': 'memory',
                'class_name': 'memory',
                'size': 8589934592,  # 8GB
            }
        )
        self.assertEqual(Node.get_ram(self.computer.id), 8589934592)

        # Test with multiple banks
        computer2 = Computer.objects.create(
            project=self.project, name='test-computer-2', uuid='87654321-4321-4321-4321-210987654321'
        )
        Node.objects.create(
            {'computer': computer2, 'level': 1, 'name': 'bank:0', 'class_name': 'memory', 'size': 4294967296}
        )
        Node.objects.create(
            {'computer': computer2, 'level': 1, 'name': 'bank:1', 'class_name': 'memory', 'size': 4294967296}
        )
        self.assertEqual(Node.get_ram(computer2.id), 8589934592)

    def test_get_mac_address(self):
        Node.objects.create(
            {
                'computer': self.computer,
                'level': 1,
                'name': 'network',
                'class_name': 'network',
                'serial': '00:11:22:33:44:55',
            }
        )
        self.assertEqual(Node.get_mac_address(self.computer.id), '001122334455')

    def test_get_storage(self):
        Node.objects.create(
            {'computer': self.computer, 'level': 1, 'name': 'disk0', 'class_name': 'disk', 'size': 500107862016}
        )
        count, total_size = Node.get_storage(self.computer.id)
        self.assertEqual(count, 1)
        self.assertEqual(total_size, 500107862016)
