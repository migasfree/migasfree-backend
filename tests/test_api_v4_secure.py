from django.test import TestCase

from migasfree.api_v4.secure import is_safe_filename


class TestIsSafeFilename(TestCase):
    """Tests for is_safe_filename function that validates filenames for security."""

    def test_safe_filename_simple(self):
        """Simple filename without special characters should be safe."""
        self.assertTrue(is_safe_filename('myfile.txt'))

    def test_safe_filename_with_path(self):
        """Normal path without dangerous patterns should be safe."""
        self.assertTrue(is_safe_filename('/tmp/myfile.txt'))

    def test_safe_filename_with_subdirectory(self):
        """Path with subdirectory should be safe."""
        self.assertTrue(is_safe_filename('/home/user/documents/file.pdf'))

    def test_unsafe_filename_with_parent_directory(self):
        """Filename with parent directory traversal (..) should be unsafe."""
        self.assertFalse(is_safe_filename('../etc/passwd'))

    def test_unsafe_filename_with_embedded_parent(self):
        """Filename with embedded parent traversal should be unsafe."""
        self.assertFalse(is_safe_filename('/home/user/../etc/shadow'))

    def test_unsafe_filename_with_backslash(self):
        """Filename with backslash should be unsafe."""
        self.assertFalse(is_safe_filename('file\\name.txt'))

    def test_unsafe_filename_with_pipe(self):
        """Filename with pipe character should be unsafe."""
        self.assertFalse(is_safe_filename('file|command'))

    def test_unsafe_filename_with_semicolon(self):
        """Filename with semicolon should be unsafe."""
        self.assertFalse(is_safe_filename('file;rm -rf /'))

    def test_unsafe_filename_with_ampersand(self):
        """Filename with ampersand should be unsafe."""
        self.assertFalse(is_safe_filename('file&command'))

    def test_unsafe_filename_with_dollar(self):
        """Filename with dollar sign should be unsafe."""
        self.assertFalse(is_safe_filename('$variable'))

    def test_unsafe_filename_with_redirect(self):
        """Filename with redirect characters should be unsafe."""
        self.assertFalse(is_safe_filename('file>output'))
        self.assertFalse(is_safe_filename('file<input'))

    def test_unsafe_filename_dev(self):
        """Filename in /dev/ should be unsafe."""
        self.assertFalse(is_safe_filename('/dev/null'))

    def test_unsafe_filename_proc(self):
        """Filename in /proc/ should be unsafe."""
        self.assertFalse(is_safe_filename('/proc/self/environ'))

    def test_unsafe_filename_sys(self):
        """Filename in /sys/ should be unsafe."""
        self.assertFalse(is_safe_filename('/sys/kernel/debug'))

    def test_safe_filename_empty(self):
        """Empty filename should be considered safe (no dangerous patterns)."""
        self.assertTrue(is_safe_filename(''))

    def test_safe_filename_with_spaces(self):
        """Filename with spaces should be safe."""
        self.assertTrue(is_safe_filename('/tmp/my file with spaces.txt'))

    def test_safe_filename_with_unicode(self):
        """Filename with unicode characters should be safe."""
        self.assertTrue(is_safe_filename('/tmp/archivo_español.txt'))
