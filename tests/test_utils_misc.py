from datetime import datetime

from migasfree.utils import decode_set, hash_args, to_heatmap


class TestToHeatmap:
    def test_basic_conversion(self):
        results = [
            {'day': datetime(2024, 1, 15), 'count': 5},
            {'day': datetime(2024, 1, 16), 'count': 10},
        ]
        expected = [['2024-01-15', 5], ['2024-01-16', 10]]

        assert to_heatmap(results) == expected

    def test_empty_results(self):
        results = []

        assert to_heatmap(results) == []

    def test_custom_range_name(self):
        results = [
            {'month': datetime(2024, 1, 1), 'count': 100},
            {'month': datetime(2024, 2, 1), 'count': 200},
        ]
        expected = [['2024-01-01', 100], ['2024-02-01', 200]]

        assert to_heatmap(results, range_name='month') == expected

    def test_single_result(self):
        results = [{'day': datetime(2024, 6, 15), 'count': 42}]
        expected = [['2024-06-15', 42]]

        assert to_heatmap(results) == expected


class TestHashArgs:
    def test_same_args_same_hash(self):
        args1 = (1, 2, 3)
        kwargs1 = {'a': 1, 'b': 2}

        hash1 = hash_args(args1, kwargs1)
        hash2 = hash_args(args1, kwargs1)

        assert hash1 == hash2

    def test_different_args_different_hash(self):
        hash1 = hash_args((1, 2, 3), {'a': 1})
        hash2 = hash_args((1, 2, 4), {'a': 1})

        assert hash1 != hash2

    def test_different_kwargs_different_hash(self):
        hash1 = hash_args((1, 2, 3), {'a': 1})
        hash2 = hash_args((1, 2, 3), {'a': 2})

        assert hash1 != hash2

    def test_empty_args_and_kwargs(self):
        result = hash_args((), {})

        assert isinstance(result, str)
        assert len(result) == 32  # MD5 hex digest is 32 characters


class TestDecodeSet:
    def test_decode_bytes_to_string(self):
        value = {b'item1', b'item2', b'item3'}
        result = decode_set(value)

        assert result == {'item1', 'item2', 'item3'}

    def test_empty_set(self):
        value = set()
        result = decode_set(value)

        assert result == set()

    def test_single_item(self):
        value = {b'single'}
        result = decode_set(value)

        assert result == {'single'}
