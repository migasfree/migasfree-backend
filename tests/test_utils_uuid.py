from migasfree.utils import uuid_change_format, uuid_validate


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


class TestUuidValidate:
    def test_formats_32_char_uuid(self):
        uuid = '12345678123412341234123456789012'
        expected = '12345678-1234-1234-1234-123456789012'

        assert uuid_validate(uuid) == expected

    def test_returns_36_char_uuid_unchanged(self):
        uuid = '12345678-1234-1234-1234-123456789012'

        assert uuid_validate(uuid) == uuid

    def test_returns_short_uuid_unchanged(self):
        uuid = '12345'

        assert uuid_validate(uuid) == uuid
