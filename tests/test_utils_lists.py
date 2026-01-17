import pytest

from migasfree.utils import (
    cmp,
    list_common,
    list_difference,
    remove_duplicates_preserving_order,
    sort_depends,
    to_list,
)


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
        text = ''
        result = to_list(text)

        assert result == []

    def test_one_word(self):
        text = 'Hello'
        result = to_list(text)

        assert result == ['Hello']

    def test_multiple_words_with_spaces(self):
        text = 'Hello world how are you?'
        result = to_list(text)

        assert result == ['Hello', 'world', 'how', 'are', 'you?']

    def test_one_word_with_trailing_space(self):
        text = 'Hello '
        result = to_list(text)

        assert result == ['Hello']

    def test_one_word_with_trailing_newline(self):
        text = 'Hello\n'
        result = to_list(text)

        assert result == ['Hello']

    def test_multiple_words_with_spaces_and_newlines(self):
        text = 'Hello\nworld\n\nhow are you?'
        result = to_list(text)

        assert result == ['Hello', 'world', 'how', 'are', 'you?']


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


class TestSets:
    def test_list_difference(self):
        l1 = [1, 2, 3, 4]
        l2 = [3, 4, 5, 6]
        result = list_difference(l1, l2)

        assert result == [1, 2]

    def test_list_difference_empty(self):
        l1 = []
        l2 = [1, 2, 3]
        result = list_difference(l1, l2)

        assert result == []

    def test_list_common(self):
        l1 = [1, 2, 3, 4]
        l2 = [3, 4, 5, 6]
        result = list_common(l1, l2)

        assert result == [3, 4]

    def test_list_common_empty(self):
        l1 = []
        l2 = [1, 2, 3]
        result = list_common(l1, l2)

        assert result == []

    def test_list_common_all(self):
        l1 = [1, 2, 3]
        l2 = [1, 2, 3]
        result = list_common(l1, l2)

        assert result == [1, 2, 3]

    def test_list_difference_set_operations(self):
        l1 = [1, 2, 3]
        l2 = {1, 2, 3}
        result = list_difference(l1, l2)

        assert result == []

    def test_list_common_set_operations(self):
        l1 = [1, 2, 3]
        l2 = {1, 2, 3}
        result = list_common(l1, l2)

        assert result == [1, 2, 3]


class TestSortDepends:
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
