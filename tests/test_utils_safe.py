from django.test import SimpleTestCase

from migasfree.utils import is_safe_url


class TestIsSafeUrl(SimpleTestCase):
    def test_safe_urls(self):
        self.assertTrue(is_safe_url('http://google.com'))
        self.assertTrue(is_safe_url('https://example.com/foo/bar'))
        self.assertTrue(is_safe_url('http://8.8.8.8'))

    def test_unsafe_urls(self):
        # Localhost
        self.assertFalse(is_safe_url('http://localhost'))
        self.assertFalse(is_safe_url('http://127.0.0.1'))
        self.assertFalse(is_safe_url('http://127.0.0.1:8000'))

        # Private IPs
        self.assertFalse(is_safe_url('http://192.168.1.1'))
        self.assertFalse(is_safe_url('http://10.0.0.1'))
        self.assertFalse(is_safe_url('http://172.16.0.1'))

        # Specialized
        self.assertFalse(is_safe_url('http://0.0.0.0'))
        self.assertFalse(is_safe_url('file:///etc/passwd'))
        self.assertFalse(is_safe_url('ftp://google.com'))
        self.assertFalse(is_safe_url('javascript:alert(1)'))
