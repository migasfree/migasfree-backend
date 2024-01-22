
import pytest

from datetime import datetime, timedelta

from migasfree.utils import (
    time_horizon, replace_keys, merge_dicts, sort_depends,
    get_client_ip, uuid_change_format, remove_empty_elements_from_dict,
    remove_duplicates_preserving_order, to_list,
)


class TestTimeHorizon:

    # Returns a date object with the correct delay added, excluding weekends.
    def test_correct_delay_excluding_weekends(self):
        date = datetime(2024, 1, 8)  # Monday
        delay = 5
        expected_date = date + timedelta(days=7)  # Expected date is 15th January 2024 (Monday)
        assert time_horizon(date, delay) == expected_date

    # Returns a date object with a delay of 0.
    def test_delay_zero(self):
        date = datetime(2024, 1, 8)  # Monday
        delay = 0
        assert time_horizon(date, delay) == date

    # Returns a date object with a delay of -1.
    def test_delay_negative_one(self):
        date = datetime(2024, 1, 8)  # Monday
        delay = -1
        expected_date = date - timedelta(days=3)  # Expected date is 5th January 2024 (Friday)
        assert time_horizon(date, delay) == expected_date

    # Returns a date object with a delay of -365.
    def test_delay_negative_365(self):
        date = datetime(2024, 1, 8)  # Monday
        delay = -365
        expected_date = date - timedelta(days=(365 + 146))  # Expected date is 15th August 2022 (Monday)
        assert time_horizon(date, delay) == expected_date


class TestReplaceKeys:

    # Replaces keys in a dictionary with their corresponding aliases
    def test_replaces_keys_with_aliases(self):
        data = [{'name': 'John', 'age': 25}, {'name': 'Jane', 'age': 30}]
        aliases = {'name': 'alias_name', 'age': 'alias_age'}
        expected_result = [{'alias_name': 'John', 'alias_age': 25}, {'alias_name': 'Jane', 'alias_age': 30}]

        result = replace_keys(data, aliases)

        assert result == expected_result

    # Handles empty input data gracefully
    def test_handles_empty_input_data(self):
        data = []
        aliases = {'name': 'alias_name', 'age': 'alias_age'}
        expected_result = []

        result = replace_keys(data, aliases)

        assert result == expected_result

    # Handles empty aliases gracefully
    def test_handles_empty_aliases(self):
        data = [{'name': 'John', 'age': 25}, {'name': 'Jane', 'age': 30}]
        aliases = {}
        expected_result = [{'name': 'John', 'age': 25}, {'name': 'Jane', 'age': 30}]

        result = replace_keys(data, aliases)

        assert result == expected_result

    # Handles input data with nested dictionaries
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

    # Merge two dictionaries with non-empty lists as values
    def test_merge_dicts_non_empty_lists(self):
        dict1 = {'a': [1, 2, 3], 'b': [4, 5, 6]}
        dict2 = {'b': [7, 8, 9], 'c': [10, 11, 12]}

        result = merge_dicts(dict1, dict2)

        assert result == {'a': [1, 2, 3], 'b': [4, 5, 6, 7, 8, 9], 'c': [10, 11, 12]}

    # Merge two dictionaries with empty lists as values
    def test_merge_dicts_empty_lists(self):
        dict1 = {'a': [], 'b': []}
        dict2 = {'b': [], 'c': []}

        result = merge_dicts(dict1, dict2)

        assert result == {'a': [], 'b': [], 'c': []}

    # Merge three or more dictionaries with non-empty lists as values
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

    # Merge dictionaries with None values
    def test_merge_dicts_none_values(self):
        dict1 = {'a': [1, 2, 3], 'b': None}
        dict2 = {'b': [4, 5, 6], 'c': None}

        result = merge_dicts(dict1, dict2)

        assert result == {'a': [1, 2, 3], 'b': [4, 5, 6], 'c': None}

    # Merge dictionaries with non-dict values
    def test_merge_dicts_non_dict_values(self):
        dict1 = {'a': [1, 2, 3], 'b': 'hello'}
        dict2 = {'b': [4, 5, 6], 'c': 123}

        result = merge_dicts(dict1, dict2)

        assert result == {'a': [1, 2, 3], 'b': [4, 5, 6], 'c': 123}

    # Returns a sorted list of items based on their dependencies
    def test_returns_sorted_list(self):
        data = {
            'item1': [],
            'item2': [],
            'item3': [],
            'item4': [],
        }
        assert sort_depends(data) == ['item1', 'item2', 'item3', 'item4']

    # Handles circular dependencies by raising a ValueError
    def test_handles_circular_dependencies(self):
        data = {
            'item1': ['item2'],
            'item2': ['item3'],
            'item3': ['item1'],
        }
        with pytest.raises(ValueError):
            sort_depends(data)

    # Handles empty input by returning an empty list
    def test_handles_empty_input(self):
        data = {}
        assert sort_depends(data) == []

    # Handles input with a single item and no dependencies
    def test_handles_single_item_no_dependencies(self):
        data = {
            'item1': [],
        }
        assert sort_depends(data) == ['item1']

    # Handles input with multiple items and no dependencies
    def test_handles_multiple_items_no_dependencies(self):
        data = {
            'item1': [],
            'item2': [],
            'item3': [],
        }
        assert sort_depends(data) == ['item1', 'item2', 'item3']

    # Handles input with multiple items and some dependencies
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

    # should return an empty dictionary when given an empty dictionary
    def test_empty_dictionary(self):
        dic = {}
        result = remove_empty_elements_from_dict(dic)
        assert result == {}

    # should return the same dictionary when given a non-empty dictionary with no empty values
    def test_non_empty_dictionary(self):
        dic = {
            "name": "John",
            "age": 30,
            "city": "New York",
            "country": "USA"
        }
        result = remove_empty_elements_from_dict(dic)
        assert result == dic

    # should return a dictionary with only non-empty key-value pairs when given a dictionary with empty values
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

    # should handle nested dictionaries with empty values
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

    # The function correctly removes duplicates from a list with no duplicates.
    def test_no_duplicates(self):
        # Arrange
        seq = [1, 2, 3, 4, 5]

        # Act
        result = remove_duplicates_preserving_order(seq)

        # Assert
        assert result == [1, 2, 3, 4, 5]

    # The function correctly removes duplicates from a list with multiple duplicates.
    def test_multiple_duplicates(self):
        # Arrange
        seq = [1, 2, 3, 2, 4, 3, 5, 4]

        # Act
        result = remove_duplicates_preserving_order(seq)

        # Assert
        assert result == [1, 2, 3, 4, 5]

    # The function correctly removes duplicates from a list with only one element.
    def test_single_element(self):
        # Arrange
        seq = [1]

        # Act
        result = remove_duplicates_preserving_order(seq)

        # Assert
        assert result == [1]

    # The function correctly handles an empty list.
    def test_empty_list(self):
        # Arrange
        seq = []

        # Act
        result = remove_duplicates_preserving_order(seq)

        # Assert
        assert result == []

    # The function correctly handles a list with None values.
    def test_none_values(self):
        # Arrange
        seq = [1, None, 2, None, 3]

        # Act
        result = remove_duplicates_preserving_order(seq)

        # Assert
        assert result == [1, None, 2, 3]

    # The function correctly handles a list with only None values.
    def test_only_none_values(self):
        # Arrange
        seq = [None, None, None]

        # Act
        result = remove_duplicates_preserving_order(seq)

        # Assert
        assert result == [None]


class TestToList:

    # should return an empty list when given an empty string
    def test_empty_string(self):
        text = ""
        result = to_list(text)
        assert result == []

    # should return a list with one element when given a string with one word
    def test_one_word(self):
        text = "Hello"
        result = to_list(text)
        assert result == ["Hello"]

    # should return a list with multiple elements when given a string with multiple words separated by spaces
    def test_multiple_words_with_spaces(self):
        text = "Hello world how are you?"
        result = to_list(text)
        assert result == ["Hello", "world", "how", "are", "you?"]

    # should return a list with one element when given a string with one word and a trailing space
    def test_one_word_with_trailing_space(self):
        text = "Hello "
        result = to_list(text)
        assert result == ["Hello"]

    # should return a list with one element when given a string with one word and a trailing new line
    def test_one_word_with_trailing_newline(self):
        text = "Hello\n"
        result = to_list(text)
        assert result == ["Hello"]

    # should return a list with multiple elements when given a string with multiple words separated by multiple spaces
    # and new lines
    def test_multiple_words_with_spaces_and_newlines(self):
        text = "Hello\nworld\n\nhow are you?"
        result = to_list(text)
        assert result == ["Hello", "world", "how", "are", "you?"]
