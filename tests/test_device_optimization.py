import json

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from migasfree.client.models import Computer
from migasfree.core.models import Attribute, Platform, Project, Property, Scope, UserProfile
from migasfree.device.models import (
    Capability,
    Connection,
    Device,
    Logical,
    Manufacturer,
    Model,
    Type,
)


class TestDeviceOptimization(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            username='admin_test', email='test@test.com', password='test', is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

        self.device_type = Type.objects.create(name='PRINTER')
        self.capability = Capability.objects.create(name='PRINTING')
        self.manufacturer = Manufacturer.objects.create(name='HP')
        self.connection = Connection.objects.create(name='USB', device_type=self.device_type)
        self.dev_model = Model.objects.create(
            name='LaserJet Pro', manufacturer=self.manufacturer, device_type=self.device_type
        )
        self.dev_model.connections.set([self.connection])

        # Create multiple devices for N+1 testing
        self.devices = []
        for i in range(10):
            device = Device.objects.create(
                name=f'Printer_{i}',
                model=self.dev_model,
                connection=self.connection,
                data=json.dumps({'LOCATION': f'Office_{i}', 'NAME': f'P_{i}'}),
            )
            self.devices.append(device)

        # Create a computer and associate with some devices
        self.platform = Platform.objects.create(name='Linux')
        self.project = Project(name='PROJ-TEST', pms='apt', architecture='x86_64', platform=self.platform)
        self.project.save()
        self.computer = Computer(name='PC-TEST', project=self.project, uuid='test-uuid', status='intended')
        self.computer.save()
        self.prop = Property(name='PROP-TEST', prefix='999')
        self.prop.save()
        self.attribute = Attribute(property_att=self.prop, value='VALUE-TEST')
        self.attribute.save()
        self.computer.sync_attributes.add(self.attribute)

        # Mark devices as available for this attribute
        for device in self.devices[:5]:
            device.available_for_attributes.add(self.attribute)
            # Create a logical device to ensure annotations have something to count
            Logical.objects.create(device=device, capability=self.capability).attributes.add(self.attribute)

    def test_device_fts_search(self):
        """Verifies that TrigramIndex search works for name and data fields."""
        # Search by name
        response = self.client.get(reverse('device-list'), {'search': 'Printer_3'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)

        # Search by data field (LOCATION)
        response = self.client.get(reverse('device-list'), {'search': 'Office_7'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)

    def test_device_n_plus_one_prevention(self):
        """Ensures listing devices uses a constant number of queries."""
        # Warm up cache if needed (though Django tests usually start fresh)
        self.client.get(reverse('device-list'))

        with self.assertNumQueries(
            4
        ):  # Exact count based on my previous verification (4 queries now due to optimizations)
            response = self.client.get(reverse('device-list'))
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_device_with_metadata_annotation(self):
        """Verifies total_computers_annotated correctness via Manager."""
        qs = Device.objects.with_metadata(self.user)
        # Device 0 should have 1 computer (from the logical device linked to computer)
        device_0 = qs.get(name='Printer_0')
        self.assertEqual(device_0.total_computers_annotated, 1)

        # Device 7 should have 0 computers (no logical device created for it)
        device_7 = qs.get(name='Printer_7')
        self.assertEqual(device_7.total_computers_annotated, 0)

    def test_device_available_skinny_view(self):
        """Verifies the refactored available action logic."""
        url = reverse('device-available')
        response = self.client.get(url, {'cid': self.computer.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # We made 5 devices available for the computer's attribute
        # Verify specific device is in results
        data = response.json()
        results = data.get('results', data)
        names = [d['name'] for d in results]
        self.assertEqual(len(results), 5)
        self.assertIn('Printer_0', names)
        self.assertNotIn('Printer_7', names)

    def test_device_scope_filtering(self):
        """Verifies that scope() method restricts access correctly."""
        # Create a non-superuser with a scope preference
        user_limited = UserProfile(username='limited', email='lim@test.com', password='test')
        user_limited.save()
        test_scope = Scope(user=user_limited, name='SCOPE-TEST')
        test_scope.save()
        user_limited.scope_preference = test_scope
        user_limited.save()

        # Without any attribute permissions, it should see 0 devices (scope() behavior)
        qs = Device.objects.scope(user_limited)
        self.assertEqual(qs.count(), 0)

        # Grant access to the attribute (simulate it being in user's scope)
        # In Migasfree, get_attributes() usually returns attributes linked to computers in the user's scope.
        # For simplicity in this test, we can mock or ensure the logic returns the attribute.
        # However, Device.objects.scope(userprofile) uses logical__attributes__in=userprofile.get_attributes().
        # Let's ensure get_attributes() returns our attribute.

        # Associate the attribute with the scope
        test_scope.included_attributes.add(self.attribute)

        # Re-fetch or ensure cache is not an issue
        qs = Device.objects.scope(user_limited)
        # Device 0 is linked to Logical device which is linked to self.attribute
        self.assertIn(self.devices[0], qs)
