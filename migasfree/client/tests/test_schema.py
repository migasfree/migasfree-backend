import json

from graphene_django.utils.testing import GraphQLTestCase

from migasfree.client.models import Computer, Fault, FaultDefinition, PackageHistory
from migasfree.core.models import Package, Platform, Project, Store
from migasfree.device.models import (
    Capability,
    Connection,
    Device,
    Logical,
    Manufacturer,
)
from migasfree.device.models import (
    Model as DeviceModel,
)
from migasfree.device.models import (
    Type as DeviceType,
)
from migasfree.schema import schema


class ClientSchemaTestCase(GraphQLTestCase):
    GRAPHQL_SCHEMA = schema

    def setUp(self):
        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(
            name='TestProject', platform=self.platform, pms='migasfree.pms.apt.Apt', architecture='amd64'
        )
        self.computer = Computer.objects.create(name='TestComputer', project=self.project, uuid='test-uuid-client')
        self.store = Store.objects.create(name='TestStore', project=self.project)

        # Setup for Software History
        self.package = Package.objects.create(
            fullname='test-package',
            name='test-package',
            version='1.0',
            architecture='amd64',
            project=self.project,
            store=self.store,
        )
        PackageHistory.objects.create(computer=self.computer, package=self.package)

        # Setup for Faults
        self.fault_def = FaultDefinition.objects.create(name='TestFault')
        Fault.objects.create(computer=self.computer, definition=self.fault_def, result='test result')

        # Setup for Devices (Simplified recursive deps)
        # Manufacturer -> Model -> Device -> Logical
        self.manufacturer = Manufacturer.objects.create(name='TestManufacturer')
        self.device_type = DeviceType.objects.create(name='TestType')
        self.model = DeviceModel.objects.create(
            name='TestModel', manufacturer=self.manufacturer, device_type=self.device_type
        )
        self.connection = Connection.objects.create(name='TestConnection', device_type=self.device_type)
        self.device = Device.objects.create(name='TestDevice', model=self.model, connection=self.connection, data='{}')
        self.capability = Capability.objects.create(name='TestCapability')
        self.logical = Logical.objects.create(device=self.device, capability=self.capability)

        # Link Logical to Computer (usually done via attributes or manually for test if resolver uses logical_devices method which filters by attributes)
        # Computer.logical_devices uses sync_attributes. We need to associate Logical.attributes with Computer.sync_attributes
        # Or simpler: Computer.logical_devices() filters Logical objects where attributes in computer.sync_attributes.
        # But Logical objects have attributes.
        # Let's see Computer.logical_devices implementation:
        # return Logical.objects.filter(attributes__in=attributes).distinct()

        # So we need to add a common attribute to both Computer (as sync_attribute) and Logical (as attribute)
        from migasfree.core.models import Attribute, Property

        self.prop = Property.objects.create(name='TestProp', prefix='TST')
        self.attr = Attribute.objects.create(property_att=self.prop, value='test')

        self.computer.sync_attributes.set([self.attr])
        self.logical.attributes.set([self.attr])

        # Setup for Errors
        from migasfree.client.models import Error

        Error.objects.create(computer=self.computer, project=self.project, description='Test error')

        # Setup for Tags (ServerAttribute)
        from migasfree.core.models import ServerAttribute

        self.tag_prop = Property.objects.create(name='TestTag', prefix='TAG', sort='server')
        self.tag = ServerAttribute.objects.create(property_att=self.tag_prop, value='test-tag')
        self.computer.tags.add(self.tag)

        # Setup for Hardware (Node hierarchy)
        from migasfree.hardware.models import Node

        self.root_node = Node.objects.create(
            data={
                'computer': self.computer,
                'name': 'computer',  # This is lshw 'id'
                'class_name': 'system',
                'description': 'Computer',
                'level': 0,
            }
        )

        self.cpu_node = Node.objects.create(
            data={
                'computer': self.computer,
                'parent': self.root_node,
                'name': 'cpu',
                'class_name': 'processor',
                'description': 'CPU',
                'level': 1,
            }
        )

    def test_computer_query(self):
        response = self.query(
            f"""
            query {{
                computer(id: "{self.computer.id}") {{
                    id
                    name
                    uuid
                    project {{
                        name
                    }}
                    softwareHistory {{
                        package {{
                            name
                        }}
                    }}
                    faults {{
                        result
                    }}
                    devices {{
                        name
                        device {{
                            name
                            model {{
                                name
                                manufacturer {{
                                    name
                                }}
                                deviceType {{
                                    name
                                }}
                            }}
                            connection {{
                                name
                            }}
                        }}
                    }}
                    errors {{
                        description
                    }}
                    attributes {{
                        value
                        propertyAtt {{
                            name
                        }}
                    }}
                    tags {{
                        value
                    }}
                    hardware {{
                        id
                        name
                        description
                        children {{
                            name
                            description
                        }}
                    }}
                }}
            }}
            """
        )

        content = json.loads(response.content)
        self.assertResponseNoErrors(response)

        data = content['data']['computer']
        self.assertEqual(data['name'], 'TestComputer')
        self.assertEqual(data['uuid'], 'test-uuid-client')
        self.assertEqual(data['project']['name'], 'TestProject')

        # Check enriched data
        self.assertEqual(data['softwareHistory'][0]['package']['name'], 'test-package')
        self.assertEqual(len(data['faults']), 1)
        self.assertEqual(data['devices'][0]['name'], 'TestCapability')

        # Check new fields
        self.assertEqual(len(data['errors']), 1)
        self.assertEqual(data['errors'][0]['description'], 'Test error')

        # Check attributes (should include 'test' from setUp)
        attributes_values = [attr['value'] for attr in data['attributes']]
        self.assertIn('test', attributes_values)

        # Check tags
        self.assertEqual(len(data['tags']), 1)
        self.assertEqual(data['tags'][0]['value'], 'test-tag')

        # Check Hardware
        self.assertEqual(data['hardware']['name'], 'computer')
        self.assertEqual(data['hardware']['children'][0]['name'], 'cpu')

    def test_catalog_queries(self):
        response = self.query(
            """
            query {
                allManufacturers {
                    name
                }
                allDeviceModels {
                    name
                }
                allDeviceTypes {
                    name
                }
                allDevices {
                    name
                }
                allPackages {
                    name
                }
                allFaultDefinitions {
                    name
                }
            }
            """
        )

        content = json.loads(response.content)
        self.assertResponseNoErrors(response)

        data = content['data']
        self.assertEqual(data['allManufacturers'][0]['name'], 'TestManufacturer')
        self.assertEqual(data['allDeviceModels'][0]['name'], 'TestModel')
        self.assertEqual(data['allDeviceTypes'][0]['name'], 'TestType')
        self.assertEqual(data['allDevices'][0]['name'], 'TestDevice')
        self.assertEqual(data['allPackages'][0]['name'], 'test-package')
        self.assertEqual(data['allFaultDefinitions'][0]['name'], 'TestFault')
