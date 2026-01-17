from migasfree.utils import escape_format_string, normalize_line_breaks


class TestEscapeFormatString:
    def test_escape_curly_braces(self):
        text = 'Hello {name}!'
        result = escape_format_string(text)

        assert result == 'Hello {{name}}!'

    def test_escape_multiple_curly_braces(self):
        text = '{greeting} {name}, you have {count} messages'
        result = escape_format_string(text)

        assert result == '{{greeting}} {{name}}, you have {{count}} messages'

    def test_no_curly_braces(self):
        text = 'Hello World!'
        result = escape_format_string(text)

        assert result == 'Hello World!'

    def test_empty_string(self):
        text = ''
        result = escape_format_string(text)

        assert result == ''

    def test_nested_braces(self):
        text = '{{already_escaped}}'
        result = escape_format_string(text)

        assert result == '{{{{already_escaped}}}}'


class TestNormalizeLineBreaks:
    def test_normalize_crlf_to_lf(self):
        text = 'Hello\r\nWorld\r\n'
        result = normalize_line_breaks(text)

        assert result == 'Hello\nWorld\n'

    def test_lf_unchanged(self):
        text = 'Hello\nWorld\n'
        result = normalize_line_breaks(text)

        assert result == 'Hello\nWorld\n'

    def test_no_line_breaks(self):
        text = 'Hello World'
        result = normalize_line_breaks(text)

        assert result == 'Hello World'

    def test_empty_string(self):
        text = ''
        result = normalize_line_breaks(text)

        assert result == ''

    def test_none_input(self):
        text = None
        result = normalize_line_breaks(text)

        assert result is None

    def test_mixed_line_breaks(self):
        text = 'Line1\r\nLine2\nLine3\r\nLine4'
        result = normalize_line_breaks(text)

        assert result == 'Line1\nLine2\nLine3\nLine4'
