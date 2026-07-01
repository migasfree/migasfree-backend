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
Service for copying InternalSource deployments between projects.

This service handles the full cascade copy:
  1. Resolve or create the equivalent Store in the target project.
  2. Copy the physical package file with shutil.copy2.
  3. Create the Package DB record in the target project.
  4. Resolve or create PackageSets in the target project.
  5. Create the new InternalSource with all its relations.
  6. Trigger repository metadata generation.
"""

import logging
import shutil
from datetime import date

from django.db import transaction

from ..models import InternalSource, Package, PackageSet, Store

logger = logging.getLogger('migasfree')


class DeploymentCopyService:
    """
    Copies an InternalSource deployment to a target project.

    Usage::

        result = DeploymentCopyService(deployment, target_project).copy()
        if result['created']:
            print(f"Deployment {result['deployment_name']} created")
        else:
            print(f"Skipped: {result['skipped_name']} already exists")
    """

    def __init__(self, deployment, target_project):
        self.source = deployment       # InternalSource to copy from
        self.target = target_project   # Project destination
        self._store_map = {}           # {source_store_id: target_Store}

    @transaction.atomic
    def copy(self):
        """
        Performs the full copy operation atomically.

        Returns a dict with:
          - created (bool)
          - deployment_id, deployment_name (if created)
          - skipped_name (if name collision)
          - copied_packages (int)
          - copied_package_sets (int)
        """
        if InternalSource.objects.filter(
            name=self.source.name, project=self.target
        ).exists():
            logger.info(
                'Deployment copy skipped: "%s" already exists in project "%s"',
                self.source.name,
                self.target.name,
            )
            return {
                'created': False,
                'skipped_name': self.source.name,
                'copied_packages': 0,
                'copied_package_sets': 0,
            }

        # 1. Copy individual available packages
        new_packages = []
        for pkg in self.source.available_packages.all():
            new_pkg = self._copy_package(pkg)
            if new_pkg:
                new_packages.append(new_pkg)

        # 2. Copy available package sets (and their internal packages)
        new_package_sets = []
        for pset in self.source.available_package_sets.all():
            new_pset = self._copy_package_set(pset)
            if new_pset:
                new_package_sets.append(new_pset)

        # 3. Create the new deployment in the target project
        new_deploy = InternalSource(
            enabled=self.source.enabled,
            name=self.source.name,
            project=self.target,
            domain=self.source.domain,
            comment=self.source.comment,
            start_date=date.today(),
            auto_restart=self.source.auto_restart,
            schedule=self.source.schedule,
            packages_to_install=self.source.packages_to_install,
            packages_to_remove=self.source.packages_to_remove,
            default_preincluded_packages=self.source.default_preincluded_packages,
            default_included_packages=self.source.default_included_packages,
            default_excluded_packages=self.source.default_excluded_packages,
        )
        new_deploy.save()
        new_deploy.included_attributes.set(self.source.included_attributes.all())
        new_deploy.excluded_attributes.set(self.source.excluded_attributes.all())
        new_deploy.available_packages.set(new_packages)
        new_deploy.available_package_sets.set(new_package_sets)

        # 4. Trigger repository metadata generation
        try:
            from ..pms import tasks

            tasks.create_repository_metadata.apply_async(
                queue=f'pms-{new_deploy.pms().name}',
                kwargs={'payload': new_deploy.get_repository_metadata_payload()},
            )
        except Exception as e:
            logger.warning(
                'Failed to trigger metadata generation for deployment "%s": %s',
                new_deploy.name,
                e,
            )

        logger.info(
            'Deployment "%s" copied to project "%s" (id=%d, packages=%d, package_sets=%d)',
            new_deploy.name,
            self.target.name,
            new_deploy.id,
            len(new_packages),
            len(new_package_sets),
        )

        return {
            'created': True,
            'deployment_id': new_deploy.id,
            'deployment_name': new_deploy.name,
            'copied_packages': len(new_packages),
            'copied_package_sets': len(new_package_sets),
        }

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _get_or_create_target_store(self, source_store):
        """
        Returns the Store in the target project with the same name.
        Creates it if it does not exist — Store.save() creates the directory.
        Results are cached in _store_map to avoid repeated DB lookups.
        """
        if source_store.id not in self._store_map:
            target_store, created = Store.objects.get_or_create(
                name=source_store.name,
                project=self.target,
            )
            if created:
                logger.info(
                    'Store "%s" created in project "%s"',
                    source_store.name,
                    self.target.name,
                )
            self._store_map[source_store.id] = target_store
        return self._store_map[source_store.id]

    def _copy_package(self, pkg):
        """
        Copies the physical package file and creates the Package record in the
        target project. Idempotent: returns the existing Package if already present.
        Returns None if the source file does not exist (logs a warning).
        """
        existing = Package.objects.filter(
            fullname=pkg.fullname, project=self.target
        ).first()
        if existing:
            return existing

        if not pkg.store:
            logger.warning(
                'Package "%s" has no store — skipping copy to project "%s"',
                pkg.fullname,
                self.target.name,
            )
            return None

        target_store = self._get_or_create_target_store(pkg.store)

        src = Package.path(self.source.project.slug, pkg.store.slug, pkg.fullname)
        dst = Package.path(self.target.slug, target_store.slug, pkg.fullname)

        try:
            shutil.copy2(src, dst)
        except FileNotFoundError:
            logger.warning(
                'Source file not found for package "%s" — skipping copy',
                pkg.fullname,
            )
            return None

        # PackageManager.create() with file_=None skips the file write;
        # the file is already in place thanks to shutil.copy2 above.
        return Package.objects.create(
            fullname=pkg.fullname,
            name=pkg.name,
            version=pkg.version,
            architecture=pkg.architecture,
            project=self.target,
            store=target_store,
        )

    def _copy_package_set(self, pset):
        """
        Copies all packages in a PackageSet and creates the set in the target
        project. Idempotent: returns the existing PackageSet if already present.
        """
        existing = PackageSet.objects.filter(
            name=pset.name, project=self.target
        ).first()
        if existing:
            return existing

        if not pset.store:
            logger.warning(
                'PackageSet "%s" has no store — skipping copy to project "%s"',
                pset.name,
                self.target.name,
            )
            return None

        target_store = self._get_or_create_target_store(pset.store)

        new_pset = PackageSet(
            name=pset.name,
            description=pset.description,
            project=self.target,
            store=target_store,
        )
        new_pset.save()

        new_pkgs = [self._copy_package(p) for p in pset.packages.all()]
        new_pset.packages.set([p for p in new_pkgs if p])

        return new_pset
