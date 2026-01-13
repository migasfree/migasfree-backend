# Copyright (c) 2015-2026 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2026 Alberto Gacías <alberto@migasfree.org>
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
Core serializers package.

This package contains serializers organized by model/feature:
- base: Mixins and utilities
- property: Property, Attribute serializers
- platform: Platform, Project serializers
- store: Store serializers
- package: Package, PackageSet serializers
- schedule: Schedule, ScheduleDelay serializers
- deployment: Deployment, InternalSource, ExternalSource serializers
- domain: Domain, Scope serializers
- user: Group, Permission, UserProfile serializers
"""

from .base import AttributeRepresentationMixin
from .deployment import (
    DeploymentListSerializer,
    DeploymentSerializer,
    DeploymentWriteSerializer,
    DomainInfoSerializer,
    ExternalSourceSerializer,
    ExternalSourceWriteSerializer,
    InternalSourceSerializer,
    InternalSourceWriteSerializer,
)
from .domain import (
    DomainListSerializer,
    DomainSerializer,
    DomainWriteSerializer,
    ScopeInfoSerializer,
    ScopeListSerializer,
    ScopeSerializer,
    ScopeWriteSerializer,
)
from .package import (
    PackageInfoSerializer,
    PackageSerializer,
    PackageSetInfoSerializer,
    PackageSetSerializer,
    PackageSetWriteSerializer,
)
from .platform import (
    PlatformSerializer,
    ProjectInfoSerializer,
    ProjectNestedInfoSerializer,
    ProjectSerializer,
    ProjectWriteSerializer,
)
from .property import (
    AttributeInfoSerializer,
    AttributeSerializer,
    AttributeSetSerializer,
    AttributeSetWriteSerializer,
    ClientAttributeSerializer,
    ClientAttributeWriteSerializer,
    ClientPropertyInfoSerializer,
    ClientPropertySerializer,
    PropertyInfoSerializer,
    PropertySerializer,
    PropertyWriteSerializer,
    ServerAttributeSerializer,
    ServerAttributeWriteSerializer,
    ServerPropertyInfoSerializer,
    ServerPropertySerializer,
    SingularitySerializer,
    SingularityWriteSerializer,
)
from .schedule import (
    ScheduleDelaySerializer,
    ScheduleDelayWriteSerializer,
    ScheduleInfoSerializer,
    ScheduleSerializer,
    ScheduleWriteSerializer,
)
from .store import (
    StoreInfoSerializer,
    StoreSerializer,
    StoreWriteSerializer,
)
from .user import (
    ChangePasswordSerializer,
    GroupInfoSerializer,
    GroupSerializer,
    GroupWriteSerializer,
    PermissionInfoSerializer,
    PermissionSerializer,
    UserProfileInfoSerializer,
    UserProfileListSerializer,
    UserProfileSerializer,
    UserProfileWriteSerializer,
)

__all__ = [
    'AttributeInfoSerializer',
    'AttributeRepresentationMixin',
    'AttributeSerializer',
    'AttributeSetSerializer',
    'AttributeSetWriteSerializer',
    'ChangePasswordSerializer',
    'ClientAttributeSerializer',
    'ClientAttributeWriteSerializer',
    'ClientPropertyInfoSerializer',
    'ClientPropertySerializer',
    'DeploymentListSerializer',
    'DeploymentSerializer',
    'DeploymentWriteSerializer',
    'DomainInfoSerializer',
    'DomainListSerializer',
    'DomainSerializer',
    'DomainWriteSerializer',
    'ExternalSourceSerializer',
    'ExternalSourceWriteSerializer',
    'GroupInfoSerializer',
    'GroupSerializer',
    'GroupWriteSerializer',
    'InternalSourceSerializer',
    'InternalSourceWriteSerializer',
    'PackageInfoSerializer',
    'PackageSerializer',
    'PackageSetInfoSerializer',
    'PackageSetSerializer',
    'PackageSetWriteSerializer',
    'PermissionInfoSerializer',
    'PermissionSerializer',
    'PlatformSerializer',
    'ProjectInfoSerializer',
    'ProjectNestedInfoSerializer',
    'ProjectSerializer',
    'ProjectWriteSerializer',
    'PropertyInfoSerializer',
    'PropertySerializer',
    'PropertyWriteSerializer',
    'ScheduleDelaySerializer',
    'ScheduleDelayWriteSerializer',
    'ScheduleInfoSerializer',
    'ScheduleSerializer',
    'ScheduleWriteSerializer',
    'ScopeInfoSerializer',
    'ScopeListSerializer',
    'ScopeSerializer',
    'ScopeWriteSerializer',
    'ServerAttributeSerializer',
    'ServerAttributeWriteSerializer',
    'ServerPropertyInfoSerializer',
    'ServerPropertySerializer',
    'SingularitySerializer',
    'SingularityWriteSerializer',
    'StoreInfoSerializer',
    'StoreSerializer',
    'StoreWriteSerializer',
    'UserProfileInfoSerializer',
    'UserProfileListSerializer',
    'UserProfileSerializer',
    'UserProfileWriteSerializer',
]
