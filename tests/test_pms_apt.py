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
        with patch('migasfree.core.pms.apt.execute', return_value=(1, '', 'Error')):
            metadata = apt.package_metadata('/path/to/pkg.deb')
            assert metadata == {'name': None, 'version': None, 'architecture': None}

    def test_package_info_success(self):
        apt = Apt()
        with (
            patch('migasfree.core.pms.apt.execute', return_value=(0, 'Some info', '')) as mock_execute,
            patch('migasfree.core.pms.apt.subprocess.Popen') as mock_popen,
        ):
            mock_proc = mock_popen.return_value
            mock_proc.communicate.return_value = (b'Some info', None)
            mock_proc.returncode = 0

            info = apt.package_info('/path/to/pkg.deb')
            assert 'Some info' in info
            for call in mock_execute.call_args_list:
                assert call[1].get('shell', False) is False

    def test_package_info_failure(self):
        apt = Apt()
        with patch('migasfree.core.pms.apt.execute', return_value=(1, '', 'Error message')) as mock_execute:
            info = apt.package_info('/path/to/pkg.deb')
            assert info == 'Error message'
            assert mock_execute.call_args[1].get('shell', False) is False

    @patch('migasfree.core.pms.apt.os.path.basename', return_value='deploy')
    @patch('migasfree.core.pms.apt.os.path.abspath', side_effect=lambda x: x)
    @patch('migasfree.core.pms.apt.os.makedirs')
    @patch('migasfree.core.pms.apt.os.chmod')
    @patch('migasfree.core.pms.apt.open')
    @patch('migasfree.core.pms.apt.gzip.open')
    def test_create_repository_call(
        self, mock_gzip_open, mock_open, mock_chmod, mock_makedirs, mock_abspath, mock_basename
    ):
        apt = Apt()
        with (
            patch('migasfree.core.pms.apt.execute', return_value=(0, 'Filename: foo/bar', '')) as mock_execute,
            patch('migasfree.core.pms.apt.os.walk', return_value=[]),
        ):
            ret, _out, _err = apt.create_repository('/var/lib/migasfree/repo/prj/dist/deploy', 'amd64')
            assert ret == 0
            for call in mock_execute.call_args_list:
                assert call[1].get('shell', False) is False
