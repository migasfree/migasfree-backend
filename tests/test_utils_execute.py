from migasfree.utils import execute


class TestExecute:
    def test_execute_simple_command_no_shell(self):
        # Expecting shell=False default behavior
        # Simple command should work without shell
        ret, out, err = execute('echo "hello world"')
        assert ret == 0
        assert out.strip() == 'hello world'

    def test_execute_shell_feature_requires_flag(self):
        # This requires shell=True
        # With shell=False (default), this might fail or print the whole string
        # 'echo "hello" | grep "hello"' might be interpreted as echo printing that string literal
        # depending on how shlex splits it and how Popen executes it.
        # Actually without shell=True, piping | is just an argument.

        cmd = 'echo "hello" | grep "hello"'
        ret, out, err = execute(cmd, shell=True)
        assert ret == 0
        assert out.strip() == 'hello'

    def test_execute_list_command(self):
        # List command should work with shell=False
        cmd = ['echo', 'hello world']
        ret, out, err = execute(cmd)
        assert ret == 0
        assert out.strip() == 'hello world'
