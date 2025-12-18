# Copyright (c) 2025 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2025 Alberto Gacías <alberto@migasfree.org>
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

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_redis():
    """Fixture to mock Redis connection."""
    with patch('migasfree.stats.tasks.get_redis_connection') as mock:
        mock_con = MagicMock()
        mock.return_value = mock_con
        yield mock_con


@pytest.mark.django_db
class TestAddOrphanPackages:
    def test_stores_in_redis(self, mock_redis):
        """Test that orphan packages count is stored in Redis."""
        from migasfree.stats.tasks import add_orphan_packages

        add_orphan_packages()

        mock_redis.hset.assert_called_once()
        call_args = mock_redis.hset.call_args
        assert call_args[0][0] == 'migasfree:chk:orphan_packages'
        assert 'mapping' in call_args[1]
        assert call_args[1]['mapping']['target'] == 'server'
        assert call_args[1]['mapping']['level'] == 'warning'
        mock_redis.sadd.assert_called_once_with('migasfree:watch:chk', 'orphan_packages')


@pytest.mark.django_db
class TestAddOrphanPackageSets:
    def test_stores_in_redis(self, mock_redis):
        """Test that orphan package sets count is stored in Redis."""
        from migasfree.stats.tasks import add_orphan_package_sets

        add_orphan_package_sets()

        mock_redis.hset.assert_called_once()
        call_args = mock_redis.hset.call_args
        assert call_args[0][0] == 'migasfree:chk:orphan_package_sets'
        mock_redis.sadd.assert_called_once_with('migasfree:watch:chk', 'orphan_package_sets')


@pytest.mark.django_db
class TestAddUncheckedNotifications:
    def test_stores_in_redis(self, mock_redis):
        """Test that unchecked notifications count is stored in Redis."""
        from migasfree.stats.tasks import add_unchecked_notifications

        add_unchecked_notifications()

        mock_redis.hset.assert_called_once()
        call_args = mock_redis.hset.call_args
        assert call_args[0][0] == 'migasfree:chk:notifications'
        assert call_args[1]['mapping']['level'] == 'warning'
        mock_redis.sadd.assert_called_once_with('migasfree:watch:chk', 'notifications')


@pytest.mark.django_db
class TestAddUncheckedFaults:
    def test_stores_in_redis(self, mock_redis):
        """Test that unchecked faults count is stored in Redis."""
        from migasfree.stats.tasks import add_unchecked_faults

        add_unchecked_faults()

        mock_redis.hset.assert_called_once()
        call_args = mock_redis.hset.call_args
        assert call_args[0][0] == 'migasfree:chk:faults'
        assert call_args[1]['mapping']['level'] == 'critical'
        mock_redis.sadd.assert_called_once_with('migasfree:watch:chk', 'faults')


@pytest.mark.django_db
class TestAddUncheckedErrors:
    def test_stores_in_redis(self, mock_redis):
        """Test that unchecked errors count is stored in Redis."""
        from migasfree.stats.tasks import add_unchecked_errors

        add_unchecked_errors()

        mock_redis.hset.assert_called_once()
        call_args = mock_redis.hset.call_args
        assert call_args[0][0] == 'migasfree:chk:errors'
        assert call_args[1]['mapping']['level'] == 'critical'
        mock_redis.sadd.assert_called_once_with('migasfree:watch:chk', 'errors')


@pytest.mark.django_db
class TestAddGeneratingRepos:
    def test_stores_in_redis(self, mock_redis):
        """Test that generating repos count is stored in Redis."""
        from migasfree.stats.tasks import add_generating_repos

        add_generating_repos()

        mock_redis.hset.assert_called_once()
        call_args = mock_redis.hset.call_args
        assert call_args[0][0] == 'migasfree:chk:repos'
        assert call_args[1]['mapping']['level'] == 'info'
        mock_redis.sadd.assert_called_once_with('migasfree:watch:chk', 'repos')


@pytest.mark.django_db
class TestAddSynchronizingComputers:
    def test_stores_in_redis(self, mock_redis):
        """Test that synchronizing computers count is stored in Redis."""
        from migasfree.stats.tasks import add_synchronizing_computers

        add_synchronizing_computers()

        mock_redis.hset.assert_called_once()
        call_args = mock_redis.hset.call_args
        assert call_args[0][0] == 'migasfree:chk:syncs'
        assert call_args[1]['mapping']['target'] == 'computer'
        mock_redis.sadd.assert_called_once_with('migasfree:watch:chk', 'syncs')


@pytest.mark.django_db
class TestAddDelayedComputers:
    def test_stores_in_redis(self, mock_redis):
        """Test that delayed computers count is stored in Redis."""
        from migasfree.stats.tasks import add_delayed_computers

        add_delayed_computers()

        mock_redis.hset.assert_called_once()
        call_args = mock_redis.hset.call_args
        assert call_args[0][0] == 'migasfree:chk:delayed'
        mock_redis.sadd.assert_called_once_with('migasfree:watch:chk', 'delayed')


@pytest.mark.django_db
class TestGetAlerts:
    @patch('migasfree.stats.tasks.get_redis_connection')
    def test_returns_list(self, mock_redis):
        """Test that get_alerts returns a list."""
        mock_con = MagicMock()
        mock_redis.return_value = mock_con
        # hgetall returns bytes for all values
        mock_con.hgetall.return_value = {
            b'msg': b'Test',
            b'target': b'server',
            b'level': b'info',
            b'result': b'0',
            b'api': b'{}',
        }

        from migasfree.stats.tasks import get_alerts

        result = get_alerts()

        assert isinstance(result, list)


@pytest.mark.django_db
class TestAlerts:
    @patch('migasfree.stats.tasks.add_orphan_packages')
    @patch('migasfree.stats.tasks.add_orphan_package_sets')
    @patch('migasfree.stats.tasks.add_unchecked_notifications')
    @patch('migasfree.stats.tasks.add_unchecked_faults')
    @patch('migasfree.stats.tasks.add_unchecked_errors')
    @patch('migasfree.stats.tasks.add_generating_repos')
    @patch('migasfree.stats.tasks.add_synchronizing_computers')
    @patch('migasfree.stats.tasks.add_delayed_computers')
    @patch('migasfree.stats.tasks.add_active_schedule_deployments')
    @patch('migasfree.stats.tasks.add_finished_schedule_deployments')
    @patch('migasfree.stats.tasks.get_alerts')
    def test_calls_all_add_functions(
        self,
        mock_get_alerts,
        mock_finished,
        mock_active,
        mock_delayed,
        mock_sync,
        mock_repos,
        mock_errors,
        mock_faults,
        mock_notifications,
        mock_pkg_sets,
        mock_pkgs,
    ):
        """Test that alerts task calls all the add_* functions."""
        mock_get_alerts.return_value = {}

        from migasfree.stats.tasks import alerts

        alerts()

        mock_pkgs.assert_called_once()
        mock_pkg_sets.assert_called_once()
        mock_notifications.assert_called_once()
        mock_faults.assert_called_once()
        mock_errors.assert_called_once()
        mock_repos.assert_called_once()
        mock_sync.assert_called_once()
        mock_delayed.assert_called_once()
        mock_active.assert_called_once()
        mock_finished.assert_called_once()
        mock_get_alerts.assert_called_once()
