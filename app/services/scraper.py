"""
Web scraping service.
Handles content extraction with a multi-strategy fallback chain:
  1. requests  (fast, works for server-rendered pages)
  2. Selenium  (for JavaScript-heavy pages)
  3. LangChain WebBaseLoader (last resort)

Raises ScraperError with a clear message on complete failure.
"""

import time
import requests
from urllib.parse import urlparse

from langchain_community.document_loaders import WebBaseLoader

from app.utils.logger import get_logger
from app.config import SCRAPE_TIMEOUT

logger = get_logger(__name__)

_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
_MIN_CONTENT_LENGTH = 2000   # Bytes — below this, content is likely a redirect/error page


class ScraperError(Exception):
    """Raised when all scraping strategies fail."""


def _is_valid_url(url: str) -> bool:
    """Basic URL sanity check — must have scheme and netloc."""
    try:
        parts = urlparse(url)
        return parts.scheme in ("http", "https") and bool(parts.netloc)
    except Exception:
        return False


def _scrape_with_requests(url: str) -> str | None:
    """Fast strategy: plain HTTP GET."""
    try:
        response = requests.get(url, headers=_REQUEST_HEADERS, timeout=SCRAPE_TIMEOUT)
        response.raise_for_status()
        if len(response.text) >= _MIN_CONTENT_LENGTH:
            logger.info("Scraping succeeded via requests | url=%s", url)
            return response.text
        logger.debug("requests returned too little content, trying next strategy")
    except requests.RequestException as exc:
        logger.warning("requests strategy failed | error=%s", exc)
    return None


def _scrape_with_selenium(url: str) -> str | None:
    """Fallback strategy: headless Chrome for JS-rendered pages."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        options = Options()
        for arg in (
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--window-size=1920,1080",
            f"--user-agent={_REQUEST_HEADERS['User-Agent']}",
        ):
            options.add_argument(arg)

        driver = webdriver.Chrome(options=options, service=Service())
        try:
            driver.get(url)
            WebDriverWait(driver, SCRAPE_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            # Scroll to trigger lazy-loaded content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            content = driver.page_source
        finally:
            driver.quit()

        if content and len(content) >= _MIN_CONTENT_LENGTH:
            logger.info("Scraping succeeded via Selenium | url=%s", url)
            return content
        logger.debug("Selenium returned too little content")
    except Exception as exc:
        logger.warning("Selenium strategy failed | error=%s", exc)
    return None


def _scrape_with_webbaseloader(url: str) -> str | None:
    """Last-resort strategy: LangChain WebBaseLoader."""
    try:
        loader = WebBaseLoader([url])
        docs = loader.load()
        content = docs[0].page_content if docs else None
        if content and len(content) >= _MIN_CONTENT_LENGTH:
            logger.info("Scraping succeeded via WebBaseLoader | url=%s", url)
            return content
        logger.debug("WebBaseLoader returned too little content")
    except Exception as exc:
        logger.warning("WebBaseLoader strategy failed | error=%s", exc)
    return None


def scrape_url(url: str) -> str:
    """
    Public entry point: scrape a URL and return its raw HTML/text content.

    Tries three strategies in order; raises ScraperError if all fail.

    Args:
        url: The job listing page URL.

    Returns:
        Raw page content (HTML or plain text).

    Raises:
        ValueError: If the URL is malformed.
        ScraperError: If all scraping strategies fail.
    """
    if not _is_valid_url(url):
        raise ValueError(f"Invalid URL: '{url}'. Must start with http:// or https://.")

    logger.info("Starting page scrape | url=%s", url)

    for strategy in (_scrape_with_requests, _scrape_with_selenium, _scrape_with_webbaseloader):
        result = strategy(url)
        if result:
            return result

    raise ScraperError(
        "Failed to load the page using all available methods. "
        "The site may block automated access, require login, or load content via JavaScript."
    )
