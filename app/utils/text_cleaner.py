"""
Text cleaning utilities for scraped HTML content.
Pure functions — no side effects, fully testable.
"""

import re


def clean_text(raw_html: str) -> str:
    """
    Strip HTML markup and normalise whitespace from scraped web content.

    Steps:
      1. Remove <script> and <style> blocks entirely.
      2. Replace block-level tags with newlines for readability.
      3. Strip remaining HTML tags.
      4. Decode common HTML entities.
      5. Collapse excessive whitespace and blank lines.

    Args:
        raw_html: Raw HTML string from a scraped page.

    Returns:
        Clean, human-readable plain text.
    """
    if not raw_html or not isinstance(raw_html, str):
        return ""

    text = raw_html

    # Remove scripts and styles completely
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Replace block-level tags with newlines
    text = re.sub(r"</?h[1-6][^>]*>", "\n\n", text)
    text = re.sub(r"</?p[^>]*>", "\n", text)
    text = re.sub(r"<br[^>]*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>", "\n• ", text)
    text = re.sub(r"<tr[^>]*>", "\n", text)
    text = re.sub(r"</td>", " | ", text)

    # Strip remaining tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Decode HTML entities
    _entities = {
        "&nbsp;": " ",
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&apos;": "'",
        "&#39;": "'",
        "&mdash;": "—",
        "&ndash;": "–",
    }
    for entity, char in _entities.items():
        text = text.replace(entity, char)

    # Collapse whitespace (preserve intentional newlines)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def truncate(text: str, max_chars: int = 8000) -> str:
    """
    Truncate text to a maximum character count to stay within LLM context limits.

    Args:
        text: Input text.
        max_chars: Maximum allowed character count.

    Returns:
        Truncated text with a trailing ellipsis if cut.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"
