from migasfree.api_v4.secure import is_safe_filename


class TestIsSafeFilename:
    def test_alphanumeric_filename(self):
        assert is_safe_filename('example123')

    def test_filename_with_dashes_and_underscores(self):
        assert is_safe_filename('example-123')

    def test_filename_with_spaces(self):
        assert is_safe_filename('example 123')

    def test_filename_with_non_allowed_characters(self):
        assert not is_safe_filename('example!@#$%^&*()')

    def test_dangerous_patterns(self):
        assert not is_safe_filename('../file')
        assert not is_safe_filename('| file')
        assert not is_safe_filename('; file')
        assert not is_safe_filename('& file')
        assert not is_safe_filename('$ file')
        assert not is_safe_filename('> file')
        assert not is_safe_filename('< file')

    def test_reserved_filenames(self):
        assert not is_safe_filename('/dev/nbd2')
        assert not is_safe_filename('/sys/kernel/warn_count')
        assert not is_safe_filename('/proc/cpuinfo')
        assert not is_safe_filename('lost+found/xxxx')
        assert not is_safe_filename('.trash-xxxx')
        assert not is_safe_filename('.Trash-xxxx')
