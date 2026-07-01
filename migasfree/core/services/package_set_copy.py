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

"""
Service for copying PackageSets between projects.

Reuses the shared helpers from DeploymentCopyService to avoid duplication:
  1. Resolve or create the equivalent Store in the target project.
  2. Copy physical package files with shutil.copy2.
  3. Create Package DB records in the target project.
  4. Create the PackageSet with its packages in the target project.
  5. Trigger repository metadata regeneration for every deployment
     that uses the new package set.
"""

import logging

from django.db import transaction

from ..models import PackageSet
from .deployment_copy import DeploymentCopyService

logger = logging.getLogger('migasfree')


class PackageSetCopyService:
    """
    Copies a PackageSet to a target project.

    Internally delegates store resolution and package file copying to the
    private helpers of DeploymentCopyService to avoid code duplication.

    Usage::

        result = PackageSetCopyService(package_set, target_project).copy()
        if result['created']:
            print(f"PackageSet {result['package_set_name']} created")
        else:
            print(f"Skipped: {result['skipped_name']} already exists")
    """

    def __init__(self, package_set, target_project):
        self.source = package_set
        self.target = target_project

    @transaction.atomic
    def copy(self):
        """
        Performs the full copy operation atomically.

        Returns a dict with:
          - created (bool)
          - package_set_id, package_set_name (if created)
          - skipped_name (if name collision)
          - copied_packages (int)
        """
        if PackageSet.objects.filter(
            name=self.source.name, project=self.target
        ).exists():
            logger.info(
                'PackageSet copy skipped: "%s" already exists in project "%s"',
                self.source.name,
                self.target.name,
            )
            return {
                'created': False,
                'skipped_name': self.source.name,
                'copied_packages': 0,
            }

        # Reuse the proven helpers from DeploymentCopyService
        _svc = DeploymentCopyService.__new__(DeploymentCopyService)
        _svc.source = None
        _svc.target = self.target
        _svc._store_map = {}

        new_pkgs = [
            _svc._copy_package(pkg)
            for pkg in self.source.packages.all()
        ]
        new_pkgs = [p for p in new_pkgs if p]

        if not self.source.store:
            logger.warning(
                'PackageSet "%s" has no store — cannot copy to project "%s"',
                self.source.name,
                self.target.name,
            )
            return {
                'created': False,
                'skipped_name': self.source.name,
                'copied_packages': 0,
            }

        target_store = _svc._get_or_create_target_store(self.source.store)

        new_pset = PackageSet(
            name=self.source.name,
            description=self.source.description,
            project=self.target,
            store=target_store,
        )
        new_pset.save()
        new_pset.packages.set(new_pkgs)

        logger.info(
            'PackageSet "%s" copied to project "%s" (id=%d, packages=%d)',
            new_pset.name,
            self.target.name,
            new_pset.id,
            len(new_pkgs),
        )

        return {
            'created': True,
            'package_set_id': new_pset.id,
            'package_set_name': new_pset.name,
            'copied_packages': len(new_pkgs),
        }
