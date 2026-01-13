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
Core admin package.

This package contains Django admin classes organized by model/feature:
- project: Platform, Project, Store
- property: ClientProperty, ServerProperty, Singularity
- attribute: ClientAttribute, ServerAttribute, AttributeSet
- package: Package, PackageSet
- schedule: Schedule, ScheduleDelay
- deployment: Deployment, InternalSource, ExternalSource
- domain: Domain, Scope
- user: UserProfile
"""

from django.contrib import admin

from ..models import Attribute, Property

# Register simple models
admin.site.register(Attribute)
admin.site.register(Property)

# Import all admin classes to register them
from .attribute import (  # noqa: E402
    AttributeSetAdmin,
    ClientAttributeAdmin,
    ClientAttributeFilter,
    ServerAttributeAdmin,
    ServerAttributeFilter,
)
from .deployment import (  # noqa: E402
    DeploymentAdmin,
    ExternalSourceAdmin,
    InternalSourceAdmin,
)
from .domain import DomainAdmin, ScopeAdmin  # noqa: E402
from .package import PackageAdmin, PackageSetAdmin  # noqa: E402
from .project import ProjectAdmin, StoreAdmin  # noqa: E402
from .property import (  # noqa: E402
    ClientPropertyAdmin,
    ClientPropertyFilter,
    ServerPropertyAdmin,
    ServerPropertyFilter,
    SingularityAdmin,
)
from .schedule import ScheduleAdmin, ScheduleDelayLine  # noqa: E402
from .user import UserProfileAdmin  # noqa: E402

__all__ = [
    'AttributeSetAdmin',
    'ClientAttributeAdmin',
    'ClientAttributeFilter',
    'ClientPropertyAdmin',
    'ClientPropertyFilter',
    'DeploymentAdmin',
    'DomainAdmin',
    'ExternalSourceAdmin',
    'InternalSourceAdmin',
    'PackageAdmin',
    'PackageSetAdmin',
    'ProjectAdmin',
    'ScheduleAdmin',
    'ScheduleDelayLine',
    'ScopeAdmin',
    'ServerAttributeAdmin',
    'ServerAttributeFilter',
    'ServerPropertyAdmin',
    'ServerPropertyFilter',
    'SingularityAdmin',
    'StoreAdmin',
    'UserProfileAdmin',
]
