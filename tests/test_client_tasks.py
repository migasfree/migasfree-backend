import uuid

import pytest
from celery import states
from django.conf import settings
from django.test import TestCase

from migasfree.client.models import Computer
from migasfree.client.tasks import update_software_inventory
from migasfree.core.models import Platform, Project


@pytest.mark.celery(result_backend=settings.CELERY_BROKER_URL)
class TestUpdateSoftwareInventoryTask(TestCase):
    def setUp(self):
        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(
            name='Vitalinux', platform=self.platform, pms='apt', architecture='amd64'
        )
        self.computer = Computer.objects.create(
            project=self.project, name='Computer1', uuid=str(uuid.uuid4()),
        )

    def test_update_software_inventory_task_existent_computer(self):
        inventory = ['package1_1.0_amd64.deb', 'package2_2.0_amd64.deb']
        result = update_software_inventory.apply(args=(self.computer.id, inventory))

        self.assertEqual(result.status, states.SUCCESS)

    def test_update_software_inventory_task_empty_inventory(self):
        inventory = []
        result = update_software_inventory.apply(args=(self.computer.id, inventory))

        self.assertEqual(result.status, states.SUCCESS)
