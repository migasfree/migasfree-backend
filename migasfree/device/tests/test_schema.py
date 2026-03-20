import json

from graphene_django.utils.testing import GraphQLTestCase

from migasfree.core.models import Project
from migasfree.device.models import (
    Capability,
    Connection,
    Device,
    Driver,
    Manufacturer,
    Model,
    Type,
)
from migasfree.schema import schema


class DeviceSchemaTestCase(GraphQLTestCase):
    GRAPHQL_SCHEMA = schema

    def setUp(self):
        from migasfree.core.models import Platform

        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(
            name='TestProject', platform=self.platform, pms='migasfree.pms.apt.Apt', architecture='amd64'
        )

        self.device_type = Type.objects.create(name='Printer')
        self.manufacturer = Manufacturer.objects.create(name='TestManufacturer')
        self.connection = Connection.objects.create(name='TestConnection', device_type=self.device_type)

        self.model = Model.objects.create(
            name='TestModel', manufacturer=self.manufacturer, device_type=self.device_type
        )
        self.model.connections.add(self.connection)

        self.device = Device.objects.create(name='TestDevice', model=self.model, connection=self.connection)

        self.capability = Capability.objects.create(name='TestCapability')

        self.driver = Driver.objects.create(
            model=self.model, project=self.project, capability=self.capability, packages_to_install='test-driver-pkg'
        )

    def test_devices_query(self):
        response = self.query(
            """
            query {
                allDevices {
                    id
                    name
                    model {
                        name
                        manufacturer {
                            name
                        }
                    }
                    connection {
                        name
                    }
                }
            }
            """
        )

        content = json.loads(response.content)
        self.assertResponseNoErrors(response)

        data = content['data']['allDevices']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'TestDevice')
        self.assertEqual(data[0]['model']['name'], 'TestModel')
        self.assertEqual(data[0]['model']['manufacturer']['name'], 'TestManufacturer')
        self.assertEqual(data[0]['connection']['name'], 'TestConnection')

    def test_drivers_query(self):
        response = self.query(
            """
            query {
                allDrivers {
                    id
                    packagesToInstall
                    model {
                        name
                    }
                    project {
                        name
                    }
                    capability {
                        name
                    }
                }
            }
            """
        )

        content = json.loads(response.content)
        self.assertResponseNoErrors(response)

        data = content['data']['allDrivers']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['packagesToInstall'], 'test-driver-pkg')
        self.assertEqual(data[0]['model']['name'], 'TestModel')
        self.assertEqual(data[0]['project']['name'], 'TestProject')
        self.assertEqual(data[0]['capability']['name'], 'TestCapability')
