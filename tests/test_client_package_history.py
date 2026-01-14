import pytest
from django.test import TestCase

from migasfree.client.models import Computer, PackageHistory
from migasfree.core.models import Package, Platform, Project


@pytest.mark.django_db
class PackageHistoryModelTestCase(TestCase):
    def setUp(self):
        self.platform = Platform.objects.create(name='Linux')
        self.project = Project.objects.create(
            name='TestProject', pms='apt', architecture='amd64', platform=self.platform
        )
        self.computer = Computer.objects.create(
            project=self.project, name='test-computer', uuid='12345678-1234-1234-1234-123456789012'
        )
        self.package = Package.objects.create(
            fullname='test-package_1.0_amd64.deb',
            name='test-package',
            version='1.0',
            architecture='amd64',
            project=self.project,
            store=None,
        )

    def test_package_history_creation(self):
        history = PackageHistory.objects.create(computer=self.computer, package=self.package)
        self.assertEqual(history.computer, self.computer)
        self.assertEqual(history.package, self.package)
        self.assertIsNotNone(history.install_date)
        self.assertIsNone(history.uninstall_date)

    def test_package_history_str(self):
        from django.utils.translation import gettext as _

        history = PackageHistory.objects.create(computer=self.computer, package=self.package)
        expected_str = _('%s at computer %s') % (self.package.fullname, self.computer)
        self.assertEqual(str(history), expected_str)

    def test_uninstall_computer_packages(self):
        PackageHistory.objects.create(computer=self.computer, package=self.package)

        # Another package
        package2 = Package.objects.create(
            fullname='pkg2_1_all.deb', name='pkg2', version='1', architecture='all', project=self.project, store=None
        )
        PackageHistory.objects.create(computer=self.computer, package=package2)

        # Some other computer's package
        comp2 = Computer.objects.create(project=self.project, name='c2', uuid='87654321-4321-4321-4321-210987654321')
        other_history = PackageHistory.objects.create(computer=comp2, package=self.package)

        PackageHistory.uninstall_computer_packages(self.computer.id)

        self.assertEqual(self.computer.packagehistory_set.filter(uninstall_date__isnull=True).count(), 0)
        self.assertEqual(self.computer.packagehistory_set.filter(uninstall_date__isnull=False).count(), 2)

        other_history.refresh_from_db()
        self.assertIsNone(other_history.uninstall_date)

    def test_uninstall_computer_packages_invalid(self):
        with self.assertRaises(ValueError):
            PackageHistory.uninstall_computer_packages(None)
