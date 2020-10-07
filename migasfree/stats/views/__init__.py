HOURLY_RANGE = 3  # days
DAILY_RANGE = 35  # days
MONTHLY_RANGE = 18  # months

from .applications import ApplicationStatsViewSet
from .attributes import ClientAttributeStatsViewSet, ServerAttributeStatsViewSet
from .computers import ComputerStatsViewSet
from .deployments import DeploymentStatsViewSet
from .devices import DeviceStatsViewSet
from .errors import ErrorStatsViewSet
from .faults import FaultStatsViewSet
from .migrations import MigrationStatsViewSet
from .notifications import NotificationStatsViewSet
from .packages import PackageStatsViewSet
from .status_logs import StatusLogStatsViewSet
from .stores import StoreStatsViewSet
from .syncs import SyncStatsViewSet
