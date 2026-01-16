# Copyright (c) 2015-2025 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2025 Alberto Gacías <alberto@migasfree.org>
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

from .attributes import (
    AttributeSetViewSet,
    AttributeViewSet,
    ClientAttributeViewSet,
    ClientPropertyViewSet,
    PropertyViewSet,
    ServerAttributeViewSet,
    ServerPropertyViewSet,
    SingularityViewSet,
)
from .base import ExportViewSet, MigasViewSet
from .deployments import (
    DeploymentViewSet,
    ExternalSourceViewSet,
    InternalSourceViewSet,
)
from .packages import PackageSetViewSet, PackageViewSet
from .platforms import PlatformViewSet, ProjectViewSet, StoreViewSet
from .schedules import ScheduleDelayViewSet, ScheduleViewSet
from .users import (
    DomainViewSet,
    GroupViewSet,
    PermissionViewSet,
    ScopeViewSet,
    UserProfileViewSet,
)

__all__ = [
    'AttributeSetViewSet',
    'AttributeViewSet',
    'ClientAttributeViewSet',
    'ClientPropertyViewSet',
    'DeploymentViewSet',
    'DomainViewSet',
    'ExportViewSet',
    'ExternalSourceViewSet',
    'GroupViewSet',
    'InternalSourceViewSet',
    'MigasViewSet',
    'PackageSetViewSet',
    'PackageViewSet',
    'PermissionViewSet',
    'PlatformViewSet',
    'ProjectViewSet',
    'PropertyViewSet',
    'ScheduleDelayViewSet',
    'ScheduleViewSet',
    'ScopeViewSet',
    'ServerAttributeViewSet',
    'ServerPropertyViewSet',
    'SingularityViewSet',
    'StoreViewSet',
    'UserProfileViewSet',
]
