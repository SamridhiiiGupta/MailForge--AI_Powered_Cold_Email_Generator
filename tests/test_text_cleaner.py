"""
Tests for app/utils/text_cleaner.py

Run with:  pytest tests/ -v
"""

from app.utils.text_cleaner import clean_text, truncate


class TestCleanText:

    def test_strips_script_tags(self):
        html = "<html><script>alert('xss')</script><p>Hello</p></html>"
        result = clean_text(html)
        assert "alert" not in result
        assert "Hello" in result

    def test_strips_style_tags(self):
        html = "<style>body { color: red; }</style><p>World</p>"
        result = clean_text(html)
        assert "color" not in result
        assert "World" in result

    def test_decodes_html_entities(self):
        html = "<p>Tom &amp; Jerry &mdash; &quot;classic&quot;</p>"
        result = clean_text(html)
        assert "&amp;" not in result
        assert "&" in result
        assert "—" in result
        assert '"' in result

    def test_empty_input_returns_empty_string(self):
        assert clean_text("") == ""

    def test_none_like_empty_string(self):
        # Should handle edge case gracefully
        assert clean_text("   ") == ""

    def test_removes_all_html_tags(self):
        html = "<div><h1>Title</h1><ul><li>Item 1</li><li>Item 2</li></ul></div>"
        result = clean_text(html)
        assert "<" not in result
        assert "Title" in result
        assert "Item 1" in result

    def test_collapses_excessive_whitespace(self):
        html = "<p>Too   many    spaces   here</p>"
        result = clean_text(html)
        assert "  " not in result   # No double spaces


class TestTruncate:

    def test_no_truncation_when_short(self):
        text = "Hello World"
        assert truncate(text, max_chars=100) == text

    def test_truncates_long_text(self):
        text = "a" * 10_000
        result = truncate(text, max_chars=500)
        assert len(result) <= 505     # 500 chars + ellipsis
        assert result.endswith("…")

    def test_exact_limit_not_truncated(self):
        text = "x" * 500
        assert truncate(text, max_chars=500) == text

    def test_default_limit_is_8000(self):
        text = "b" * 9_000
        result = truncate(text)
        assert len(result) <= 8005
        assert result.endswith("…")
