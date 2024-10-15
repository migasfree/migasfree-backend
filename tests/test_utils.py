import pytest

from datetime import datetime, timedelta

from migasfree.utils import (
    time_horizon, replace_keys, merge_dicts, sort_depends,
    get_client_ip, uuid_change_format, remove_empty_elements_from_dict,
    remove_duplicates_preserving_order, to_list, cmp,
)


class TestTimeHorizon:

    def test_correct_delay_excluding_weekends(self):
        date = datetime(2024, 1, 8)  # Monday
        delay = 5
        expected_date = date + timedelta(days=7)  # Expected date is 15th January 2024 (Monday)
        assert time_horizon(date, delay) == expected_date

    def test_delay_zero(self):
        date = datetime(2024, 1, 8)  # Monday
        delay = 0
        assert time_horizon(date, delay) == date

    def test_delay_negative_one(self):
        date = datetime(2024, 1, 8)  # Monday
        delay = -1
        expected_date = date - timedelta(days=3)  # Expected date is 5th January 2024 (Friday)
        assert time_horizon(date, delay) == expected_date

    def test_delay_negative_365(self):
        date = datetime(2024, 1, 8)  # Monday
        delay = -365
        expected_date = date - timedelta(days=(365 + 146))  # Expected date is 15th August 2022 (Monday)
        assert time_horizon(date, delay) == expected_date


class TestReplaceKeys:

    def test_replaces_keys_with_aliases(self):
        data = [{'name': 'John', 'age': 25}, {'name': 'Jane', 'age': 30}]
        aliases = {'name': 'alias_name', 'age': 'alias_age'}
        expected_result = [{'alias_name': 'John', 'alias_age': 25}, {'alias_name': 'Jane', 'alias_age': 30}]

        result = replace_keys(data, aliases)

        assert result == expected_result

    def test_handles_empty_input_data(self):
        data = []
        aliases = {'name': 'alias_name', 'age': 'alias_age'}
        expected_result = []

        result = replace_keys(data, aliases)

        assert result == expected_result

    def test_handles_empty_aliases(self):
        data = [{'name': 'John', 'age': 25}, {'name': 'Jane', 'age': 30}]
        aliases = {}
        expected_result = [{'name': 'John', 'age': 25}, {'name': 'Jane', 'age': 30}]

        result = replace_keys(data, aliases)

        assert result == expected_result

    def test_handles_nested_dictionaries(self):
        data = [{'name': 'John', 'age': 25, 'address': {'street': '123 Main St', 'city': 'New York'}}]
        aliases = {'name': 'alias_name', 'age': 'alias_age', 'address': 'alias_address'}
        expected_result = [
            {
                'alias_name': 'John',
                'alias_age': 25,
                'alias_address': {'street': '123 Main St', 'city': 'New York'}
            }
        ]

        result = replace_keys(data, aliases)

        assert result == expected_result


class TestMergeDicts:

    def test_merge_dicts_non_empty_lists(self):
        dict1 = {'a': [1, 2, 3], 'b': [4, 5, 6]}
        dict2 = {'b': [7, 8, 9], 'c': [10, 11, 12]}

        result = merge_dicts(dict1, dict2)

        assert result == {'a': [1, 2, 3], 'b': [4, 5, 6, 7, 8, 9], 'c': [10, 11, 12]}

    def test_merge_dicts_empty_lists(self):
        dict1 = {'a': [], 'b': []}
        dict2 = {'b': [], 'c': []}

        result = merge_dicts(dict1, dict2)

        assert result == {'a': [], 'b': [], 'c': []}

    def test_merge_dicts_multiple_non_empty_lists(self):
        dict1 = {'a': [1, 2, 3], 'b': [4, 5, 6]}
        dict2 = {'b': [7, 8, 9], 'c': [10, 11, 12]}
        dict3 = {'c': [13, 14, 15], 'd': [16, 17, 18]}

        result = merge_dicts(dict1, dict2, dict3)

        assert result == {
            'a': [1, 2, 3],
            'b': [4, 5, 6, 7, 8, 9],
            'c': [10, 11, 12, 13, 14, 15],
            'd': [16, 17, 18]
        }

    def test_merge_dicts_none_values(self):
        dict1 = {'a': [1, 2, 3], 'b': None}
        dict2 = {'b': [4, 5, 6], 'c': None}

        result = merge_dicts(dict1, dict2)

        assert result == {'a': [1, 2, 3], 'b': [4, 5, 6], 'c': None}

    def test_merge_dicts_non_dict_values(self):
        dict1 = {'a': [1, 2, 3], 'b': 'hello'}
        dict2 = {'b': [4, 5, 6], 'c': 123}

        result = merge_dicts(dict1, dict2)

        assert result == {'a': [1, 2, 3], 'b': [4, 5, 6], 'c': 123}

    def test_returns_sorted_list(self):
        data = {
            'item1': [],
            'item2': [],
            'item3': [],
            'item4': [],
        }
        assert sort_depends(data) == ['item1', 'item2', 'item3', 'item4']

    def test_handles_circular_dependencies(self):
        data = {
            'item1': ['item2'],
            'item2': ['item3'],
            'item3': ['item1'],
        }
        with pytest.raises(ValueError):
            sort_depends(data)

    def test_handles_empty_input(self):
        data = {}
        assert sort_depends(data) == []

    def test_handles_single_item_no_dependencies(self):
        data = {
            'item1': [],
        }
        assert sort_depends(data) == ['item1']

    def test_handles_multiple_items_no_dependencies(self):
        data = {
            'item1': [],
            'item2': [],
            'item3': [],
        }
        assert sort_depends(data) == ['item1', 'item2', 'item3']

    def test_handles_multiple_items_with_dependencies(self):
        data = {
            'item1': ['item2'],
            'item2': ['item3'],
            'item3': [],
        }
        assert sort_depends(data) == ['item3', 'item2', 'item1']


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


class TestUuidChangeFormat:

    # Returns the same UUID if it does not have 36 characters.
    def test_returns_same_uuid_if_not_36_characters(self):
        uuid = '12345'

        assert uuid_change_format(uuid) == uuid

    # Returns the UUID in big-endian format if it has 36 characters.
    def test_returns_uuid_in_big_endian_format_if_36_characters(self):
        uuid = '12345678-1234-1234-1234-123456789012'

        assert uuid_change_format(uuid) == '78563412-3412-3412-1234-123456789012'

    # Returns an empty string if the input is an empty string.
    def test_returns_empty_string_if_input_is_empty_string(self):
        uuid = ''

        assert uuid_change_format(uuid) == ''

    # Returns None if the input is None.
    def test_returns_none_if_input_is_none(self):
        uuid = None

        assert uuid_change_format(uuid) == ''

    # Returns the same UUID if it has less than 36 characters.
    def test_returns_same_uuid_if_less_than_36_characters(self):
        uuid = '12345678-1234-1234-1234'

        assert uuid_change_format(uuid) == uuid


class TestRemoveEmptyElementsFromDict:

    def test_empty_dictionary(self):
        dic = {}
        result = remove_empty_elements_from_dict(dic)
        assert result == {}

    def test_non_empty_dictionary(self):
        dic = {
            "name": "John",
            "age": 30,
            "city": "New York",
            "country": "USA"
        }
        result = remove_empty_elements_from_dict(dic)
        assert result == dic

    def test_dictionary_with_empty_values(self):
        dic = {
            "name": "",
            "age": 30,
            "city": "",
            "country": "USA"
        }
        result = remove_empty_elements_from_dict(dic)
        expected_result = {
            "age": 30,
            "country": "USA"
        }
        assert result == expected_result

    def test_nested_dictionaries_with_empty_values(self):
        dic = {
            "name": "John",
            "age": 30,
            "address": {
                "street": "",
                "city": "New York",
                "country": ""
            }
        }
        result = remove_empty_elements_from_dict(dic)
        expected_result = {
            "name": "John",
            "age": 30,
            "address": {
                "city": "New York"
            }
        }
        assert result == expected_result

    # should handle dictionaries with empty keys
    def test_dictionary_with_empty_keys(self):
        dic = {
            "name": "John",
            "age": 30,
            "": "USA"
        }
        result = remove_empty_elements_from_dict(dic)
        expected_result = {
            "name": "John",
            "age": 30
        }
        assert result == expected_result

    # should handle dictionaries with empty string values
    def test_dictionary_with_empty_string_values(self):
        dic = {
            "name": "",
            "age": 30,
            "city": "",
            "country": ""
        }
        result = remove_empty_elements_from_dict(dic)
        expected_result = {
            "age": 30
        }
        assert result == expected_result


class TestRemoveDuplicatesPreservingOrder:

    def test_no_duplicates(self):
        seq = [1, 2, 3, 4, 5]
        result = remove_duplicates_preserving_order(seq)

        assert result == [1, 2, 3, 4, 5]

    def test_multiple_duplicates(self):
        seq = [1, 2, 3, 2, 4, 3, 5, 4]
        result = remove_duplicates_preserving_order(seq)

        assert result == [1, 2, 3, 4, 5]

    def test_single_element(self):
        seq = [1]
        result = remove_duplicates_preserving_order(seq)

        assert result == [1]

    def test_empty_list(self):
        seq = []
        result = remove_duplicates_preserving_order(seq)

        assert result == []

    def test_none_values(self):
        seq = [1, None, 2, None, 3]
        result = remove_duplicates_preserving_order(seq)

        assert result == [1, None, 2, 3]

    def test_only_none_values(self):
        seq = [None, None, None]
        result = remove_duplicates_preserving_order(seq)

        assert result == [None]


class TestToList:

    def test_empty_string(self):
        text = ""
        result = to_list(text)

        assert result == []

    def test_one_word(self):
        text = "Hello"
        result = to_list(text)

        assert result == ["Hello"]

    def test_multiple_words_with_spaces(self):
        text = "Hello world how are you?"
        result = to_list(text)

        assert result == ["Hello", "world", "how", "are", "you?"]

    def test_one_word_with_trailing_space(self):
        text = "Hello "
        result = to_list(text)

        assert result == ["Hello"]

    def test_one_word_with_trailing_newline(self):
        text = "Hello\n"
        result = to_list(text)

        assert result == ["Hello"]

    def test_multiple_words_with_spaces_and_newlines(self):
        text = "Hello\nworld\n\nhow are you?"
        result = to_list(text)

        assert result == ["Hello", "world", "how", "are", "you?"]


class TestCmp:

    def test_cmp(self):
        # a > b
        assert cmp([3, 4, 5], [2, 3, 4]) == 1
        assert cmp([7, 8, 9], [6, 7, 8]) == 1

        # a < b
        assert cmp([1, 2, 3], [4, 5, 6]) == -1
        assert cmp([-3, -2, -1], [-1, 0, 1]) == -1

        # a = b
        assert cmp([1, 2, 3], [1, 2, 3]) == 0
        assert cmp([-5, -4, -3], [-5, -4, -3]) == 0

    def test_cmp_empty_lists(self):
        assert cmp([], []) == 0

    def test_cmp_single_element_list(self):
        assert cmp([5], [2]) == 1
        assert cmp([-3], [-5]) == 1

    def test_cmp_same_length_lists(self):
        assert cmp([1, 2, 3], [4, 5, 6]) == -1
        assert cmp([-7, -6, -5], [-9, -8, -7]) == 1

    def test_cmp_different_length_lists(self):
        assert cmp([1, 2, 3], [4, 5]) == -1
        assert cmp([-3, -2], [-1, 0, 1]) == -1

    def test_cmp_negative_numbers(self):
        assert cmp([-5, -4, -3], [-6, -7, -8]) == 1
        assert cmp([-9, -10, -11], [-7, -8, -9]) == -1

    def test_cmp_zero(self):
        assert cmp([0, 0, 0], [0, 0, 0]) == 0
