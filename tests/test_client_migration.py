import pytest
from django.test import TestCase

from migasfree.client.models import Computer, Migration
from migasfree.core.models import Platform, Project


@pytest.mark.django_db
class MigrationModelTestCase(TestCase):
    def setUp(self):
        self.platform = Platform.objects.create(name='Linux')
        self.project1 = Project.objects.create(name='Project1', pms='apt', architecture='amd64', platform=self.platform)
        self.project2 = Project.objects.create(name='Project2', pms='apt', architecture='amd64', platform=self.platform)
        self.computer = Computer.objects.create(
            project=self.project1, name='test-computer', uuid='12345678-1234-1234-1234-123456789012'
        )

    def test_migration_creation(self):
        migration = Migration.objects.create(self.computer, self.project2)
        self.assertEqual(migration.computer, self.computer)
        self.assertEqual(migration.project, self.project2)
        self.assertIsNotNone(migration.created_at)

    def test_migration_str(self):
        migration = Migration.objects.create(self.computer, self.project2)
        expected_str = f'{self.computer} ({migration.created_at:%Y-%m-%d %H:%M:%S}) {self.project2}'
        self.assertEqual(str(migration), expected_str)
