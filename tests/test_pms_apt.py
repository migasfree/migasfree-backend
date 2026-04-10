from unittest.mock import patch

from migasfree.core.pms.apt import Apt


class TestApt:
    def test_package_metadata_success(self):
        apt = Apt()
        output = 'migasfree-agent_1.0.0-1_all'
        with patch('migasfree.core.pms.apt.execute', return_value=(0, output, '')) as mock_execute:
            metadata = apt.package_metadata('/path/to/pkg.deb')
            assert metadata == {'name': 'migasfree-agent', 'version': '1.0.0-1', 'architecture': 'all'}
            mock_execute.assert_called_once()
            args, kwargs = mock_execute.call_args
            assert args[0] == [
                'dpkg-deb',
                '--showformat=${Package}_${Version}_${Architecture}',
                '--show',
                '/path/to/pkg.deb',
            ]
            assert kwargs['shell'] is False

    def test_package_metadata_failure(self):
        apt = Apt()
        with patch('migasfree.core.pms.apt.execute', return_value=(1, '', 'Error')) as mock_execute:
            metadata = apt.package_metadata('/path/to/pkg.deb')
            assert metadata == {'name': None, 'version': None, 'architecture': None}

    def test_package_info_success(self):
        apt = Apt()
        with patch('migasfree.core.pms.apt.execute', return_value=(0, 'Some info', '')) as mock_execute:
            info = apt.package_info('/path/to/pkg.deb')
            assert info == 'Some info'
            assert mock_execute.call_args[1]['shell'] is True

    def test_package_info_failure(self):
        apt = Apt()
        with patch('migasfree.core.pms.apt.execute', return_value=(1, '', 'Error message')) as mock_execute:
            info = apt.package_info('/path/to/pkg.deb')
            assert info == 'Error message'

    def test_create_repository_call(self):
        apt = Apt()
        with patch('migasfree.core.pms.apt.execute', return_value=(0, 'Output', '')) as mock_execute:
            apt.create_repository('/var/lib/migasfree/repo/prj/dist/deploy', 'amd64')
            mock_execute.assert_called_once()
            args, kwargs = mock_execute.call_args
            assert 'apt-ftparchive' in args[0]
            assert kwargs['shell'] is True
