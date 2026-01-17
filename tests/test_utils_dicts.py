from migasfree.utils import (
    decode_dict,
    merge_dicts,
    remove_empty_elements_from_dict,
    replace_keys,
)


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
            {'alias_name': 'John', 'alias_age': 25, 'alias_address': {'street': '123 Main St', 'city': 'New York'}}
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

        assert result == {'a': [1, 2, 3], 'b': [4, 5, 6, 7, 8, 9], 'c': [10, 11, 12, 13, 14, 15], 'd': [16, 17, 18]}

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


class TestRemoveEmptyElementsFromDict:
    def test_empty_dictionary(self):
        dic = {}
        result = remove_empty_elements_from_dict(dic)
        assert result == {}

    def test_non_empty_dictionary(self):
        dic = {'name': 'John', 'age': 30, 'city': 'New York', 'country': 'USA'}
        result = remove_empty_elements_from_dict(dic)
        assert result == dic

    def test_dictionary_with_empty_values(self):
        dic = {'name': '', 'age': 30, 'city': '', 'country': 'USA'}
        result = remove_empty_elements_from_dict(dic)
        expected_result = {'age': 30, 'country': 'USA'}
        assert result == expected_result

    def test_nested_dictionaries_with_empty_values(self):
        dic = {'name': 'John', 'age': 30, 'address': {'street': '', 'city': 'New York', 'country': ''}}
        result = remove_empty_elements_from_dict(dic)
        expected_result = {'name': 'John', 'age': 30, 'address': {'city': 'New York'}}
        assert result == expected_result

    # should handle dictionaries with empty keys
    def test_dictionary_with_empty_keys(self):
        dic = {'name': 'John', 'age': 30, '': 'USA'}
        result = remove_empty_elements_from_dict(dic)
        expected_result = {'name': 'John', 'age': 30}
        assert result == expected_result

    # should handle dictionaries with empty string values
    def test_dictionary_with_empty_string_values(self):
        dic = {'name': '', 'age': 30, 'city': '', 'country': ''}
        result = remove_empty_elements_from_dict(dic)
        expected_result = {'age': 30}
        assert result == expected_result


class TestDecodeDict:
    def test_decode_bytes_to_string(self):
        value = {b'key1': b'value1', b'key2': b'value2'}
        result = decode_dict(value)

        assert result == {'key1': 'value1', 'key2': 'value2'}

    def test_empty_dict(self):
        value = {}
        result = decode_dict(value)

        assert result == {}

    def test_single_entry(self):
        value = {b'name': b'John'}
        result = decode_dict(value)

        assert result == {'name': 'John'}
