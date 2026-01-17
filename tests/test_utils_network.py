from migasfree.utils import get_client_ip, get_proxied_ip_address


class TestGetClientIp:
    def setup_method(self):
        class HttpRequest:
            def __init__(self):
                self.META = {}

        self.request = HttpRequest()

    # Returns the IP address from the 'REMOTE_ADDR' key in the request's META dictionary.
    def test_returns_ip_from_remote_addr(self):
        self.request.META = {'REMOTE_ADDR': '192.168.0.1'}

        assert get_client_ip(self.request) == '192.168.0.1'

    # Returns the first IP address from the 'HTTP_X_FORWARDED_FOR' key in the request's META dictionary if it exists.
    def test_returns_first_ip_from_x_forwarded_for(self):
        self.request.META = {'HTTP_X_FORWARDED_FOR': '192.168.0.1, 10.0.0.1'}

        assert get_client_ip(self.request) == '192.168.0.1'

    # Returns the correct IP address for a regular HTTP request.
    def test_returns_correct_ip_for_http_request(self):
        self.request.META = {'REMOTE_ADDR': '192.168.0.1', 'HTTP_X_FORWARDED_FOR': '10.0.0.1'}

        assert get_client_ip(self.request) == '10.0.0.1'

    # Returns None if the request object is None.
    def test_returns_none_if_request_object_is_none(self):
        self.request = None

        assert get_client_ip(self.request) is None

    # Returns None if the request's META dictionary is None.
    def test_returns_none_if_meta_dictionary_is_none(self):
        self.request.META = None

        assert get_client_ip(self.request) is None

    # Returns None if both 'REMOTE_ADDR' and 'HTTP_X_FORWARDED_FOR' keys are missing from the request's META dictionary.
    def test_returns_none_if_both_keys_are_missing(self):
        self.request.META = {}

        assert get_client_ip(self.request) is None


class TestGetProxiedIpAddress:
    def setup_method(self):
        class HttpRequest:
            def __init__(self):
                self.META = {}

        self.request = HttpRequest()

    def test_returns_remote_addr_when_no_forwarded(self):
        self.request.META = {'REMOTE_ADDR': '192.168.0.1'}

        assert get_proxied_ip_address(self.request) == '192.168.0.1'

    def test_returns_combined_ip_when_forwarded_differs(self):
        self.request.META = {'REMOTE_ADDR': '192.168.0.1', 'HTTP_X_FORWARDED_FOR': '10.0.0.1'}

        assert get_proxied_ip_address(self.request) == '192.168.0.1/10.0.0.1'

    def test_returns_single_ip_when_forwarded_equals_remote(self):
        self.request.META = {'REMOTE_ADDR': '192.168.0.1', 'HTTP_X_FORWARDED_FOR': '192.168.0.1'}

        assert get_proxied_ip_address(self.request) == '192.168.0.1'

    def test_returns_first_forwarded_ip_from_chain(self):
        self.request.META = {'REMOTE_ADDR': '192.168.0.1', 'HTTP_X_FORWARDED_FOR': '10.0.0.1, 172.16.0.1, 192.168.0.1'}

        assert get_proxied_ip_address(self.request) == '192.168.0.1/10.0.0.1'
