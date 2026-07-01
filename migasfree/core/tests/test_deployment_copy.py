# Copyright (c) 2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2026 Alberto Gacías <alberto@migasfree.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import shutil
import tempfile
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from migasfree.core.models import (
    InternalSource,
    Package,
    PackageSet,
    Platform,
    Project,
    Store,
    UserProfile,
)
from migasfree.core.services.deployment_copy import DeploymentCopyService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_platform(name='Linux'):
    return Platform.objects.get_or_create(name=name)[0]


def _make_project(name, pms='apt', architecture='amd64', platform=None):
    if platform is None:
        platform = _make_platform()
    return Project.objects.get_or_create(
        name=name,
        defaults={'pms': pms, 'architecture': architecture, 'platform': platform},
    )[0]


def _make_store(name, project):
    return Store.objects.get_or_create(name=name, project=project)[0]


def _make_deployment(name, project, **kwargs):
    deploy = InternalSource(name=name, project=project, **kwargs)
    deploy.save()
    return deploy


# ---------------------------------------------------------------------------
# Service unit tests (no physical filesystem required)
# ---------------------------------------------------------------------------

class DeploymentCopyServiceTest(TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.src_project = _make_project('src-project')
        self.dst_project = _make_project('dst-project')
        self.src_store = _make_store('main', self.src_project)
        self.deployment = _make_deployment('deploy-a', self.src_project)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    # ------------------------------------------------------------------
    # Test 1: basic copy creates deployment in destination project
    # ------------------------------------------------------------------
    def test_copy_creates_deployment(self):
        result = DeploymentCopyService(self.deployment, self.dst_project).copy()

        self.assertTrue(result['created'])
        self.assertEqual(result['deployment_name'], 'deploy-a')
        self.assertTrue(
            InternalSource.objects.filter(name='deploy-a', project=self.dst_project).exists()
        )

    # ------------------------------------------------------------------
    # Test 2: store is created in destination if missing
    # ------------------------------------------------------------------
    def test_copy_creates_store_if_missing(self):
        DeploymentCopyService(self.deployment, self.dst_project).copy()

        # No packages to copy, but a package with a store would trigger creation.
        # We verify explicitly via _get_or_create_target_store.
        svc = DeploymentCopyService(self.deployment, self.dst_project)
        target_store = svc._get_or_create_target_store(self.src_store)
        self.assertEqual(target_store.project, self.dst_project)
        self.assertEqual(target_store.name, self.src_store.name)

    # ------------------------------------------------------------------
    # Test 3: physical file is copied
    # ------------------------------------------------------------------
    @override_settings(MIGASFREE_PUBLIC_DIR='/tmp/mf_test_public', MIGASFREE_STORE_TRAILING_PATH='stores')
    @patch('migasfree.core.services.deployment_copy.shutil.copy2')
    def test_copy_copies_physical_file(self, mock_copy2):
        pkg = Package(
            fullname='foo_1.0_amd64.deb',
            name='foo',
            version='1.0',
            architecture='amd64',
            project=self.src_project,
            store=self.src_store,
        )
        # bypass store directory creation
        with patch.object(Package, 'create_dir'):
            pkg.save()

        self.deployment.available_packages.add(pkg)

        with patch('migasfree.core.pms.tasks.create_repository_metadata') as mock_meta:
            mock_meta.apply_async = MagicMock()
            DeploymentCopyService(self.deployment, self.dst_project).copy()

        self.assertTrue(mock_copy2.called)
        call_args = mock_copy2.call_args[0]
        self.assertIn('foo_1.0_amd64.deb', call_args[0])  # src path
        self.assertIn('dst-project', call_args[1])  # dst path

    # ------------------------------------------------------------------
    # Test 4: idempotent — existing package in destination is reused
    # ------------------------------------------------------------------
    @patch('migasfree.core.services.deployment_copy.shutil.copy2')
    def test_copy_idempotent_package(self, mock_copy2):
        dst_store = _make_store('main', self.dst_project)
        existing_pkg = Package(
            fullname='bar_2.0_amd64.deb',
            name='bar',
            version='2.0',
            architecture='amd64',
            project=self.dst_project,
            store=dst_store,
        )
        with patch.object(Package, 'create_dir'):
            existing_pkg.save()

        src_pkg = Package(
            fullname='bar_2.0_amd64.deb',
            name='bar',
            version='2.0',
            architecture='amd64',
            project=self.src_project,
            store=self.src_store,
        )
        with patch.object(Package, 'create_dir'):
            src_pkg.save()

        self.deployment.available_packages.add(src_pkg)

        svc = DeploymentCopyService(self.deployment, self.dst_project)
        result_pkg = svc._copy_package(src_pkg)

        # Must reuse the existing package — no file copy
        mock_copy2.assert_not_called()
        self.assertEqual(result_pkg.id, existing_pkg.id)

    # ------------------------------------------------------------------
    # Test 5: skips when name already exists in destination
    # ------------------------------------------------------------------
    def test_copy_skips_existing_deployment(self):
        _make_deployment('deploy-a', self.dst_project)  # pre-existing

        result = DeploymentCopyService(self.deployment, self.dst_project).copy()

        self.assertFalse(result['created'])
        self.assertEqual(result['skipped_name'], 'deploy-a')
        self.assertEqual(result['copied_packages'], 0)

    # ------------------------------------------------------------------
    # Test 6: start_date is reset to today
    # ------------------------------------------------------------------
    def test_copy_start_date_is_today(self):
        import datetime
        from datetime import date as real_date

        past_date = datetime.date(2020, 1, 1)
        self.deployment.start_date = past_date
        self.deployment.save()

        DeploymentCopyService(self.deployment, self.dst_project).copy()

        new_deploy = InternalSource.objects.get(name='deploy-a', project=self.dst_project)
        self.assertEqual(new_deploy.start_date, real_date.today())

    # ------------------------------------------------------------------
    # Test 7: enabled value is preserved
    # ------------------------------------------------------------------
    def test_copy_preserves_enabled(self):
        self.deployment.enabled = False
        self.deployment.save()

        DeploymentCopyService(self.deployment, self.dst_project).copy()

        new_deploy = InternalSource.objects.get(name='deploy-a', project=self.dst_project)
        self.assertFalse(new_deploy.enabled)

    # ------------------------------------------------------------------
    # Test 8: package set is copied with its packages
    # ------------------------------------------------------------------
    @patch('migasfree.core.services.deployment_copy.shutil.copy2')
    def test_copy_copies_package_set_with_packages(self, mock_copy2):
        src_pkg = Package(
            fullname='baz_1.0_amd64.deb',
            name='baz',
            version='1.0',
            architecture='amd64',
            project=self.src_project,
            store=self.src_store,
        )
        with patch.object(Package, 'create_dir'):
            src_pkg.save()

        pset = PackageSet(name='myset', project=self.src_project, store=self.src_store)
        with patch.object(PackageSet, 'clean'):
            pset.save()
        pset.packages.add(src_pkg)
        self.deployment.available_package_sets.add(pset)

        with patch('migasfree.core.pms.tasks.create_repository_metadata') as mock_meta:
            mock_meta.apply_async = MagicMock()
            result = DeploymentCopyService(self.deployment, self.dst_project).copy()

        self.assertTrue(result['created'])
        self.assertEqual(result['copied_package_sets'], 1)
        self.assertTrue(
            PackageSet.objects.filter(name='myset', project=self.dst_project).exists()
        )
        dst_pset = PackageSet.objects.get(name='myset', project=self.dst_project)
        self.assertEqual(dst_pset.packages.count(), 1)
        self.assertEqual(dst_pset.packages.first().fullname, 'baz_1.0_amd64.deb')


# ---------------------------------------------------------------------------
# API integration tests
# ---------------------------------------------------------------------------

class DeploymentCopyAPITest(APITestCase):
    def setUp(self):
        self.superuser = UserProfile.objects.create(
            username='admin',
            email='admin@localhost.com',
            password='admin',
            is_superuser=True,
            is_staff=True,
            is_active=True,
        )
        self.client.force_authenticate(user=self.superuser)

        self.src_project = _make_project('api-src')
        self.dst_project = _make_project('api-dst')
        self.deployment = _make_deployment('api-deploy', self.src_project)

    # ------------------------------------------------------------------
    # Test 9: endpoint returns 400 when source == destination
    # ------------------------------------------------------------------
    def test_copy_same_project_rejected(self):
        url = reverse('internalsource-copy', args=[self.deployment.id])
        response = self.client.post(url, {'project': self.src_project.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # Test 10: endpoint returns 400 when project param is missing
    # ------------------------------------------------------------------
    def test_copy_missing_project_rejected(self):
        url = reverse('internalsource-copy', args=[self.deployment.id])
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # Test 11: endpoint returns 200 and creates deployment
    # ------------------------------------------------------------------
    @patch.object(DeploymentCopyService, 'copy', return_value={
        'created': True,
        'deployment_id': 99,
        'deployment_name': 'api-deploy',
        'copied_packages': 0,
        'copied_package_sets': 0,
    })
    def test_copy_endpoint_success(self, mock_copy):
        url = reverse('internalsource-copy', args=[self.deployment.id])
        response = self.client.post(url, {'project': self.dst_project.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['created'])
        mock_copy.assert_called_once()
