"""
Shared pytest fixtures for the entire test suite.

Fixtures defined here are available in every test file without importing.
This file is the single source of truth for:
- API client configuration (base URL, timeout)
- Shared session lifecycle management
- Common test data factories
- Selenium WebDriver setup / teardown

pytest discovers conftest.py automatically — no import required in test files.
"""

import logging
import os

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from src.client.api_client import APIClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration constants (override via environment variables in CI)
# ---------------------------------------------------------------------------

BASE_URL: str = os.getenv("BASE_URL", "https://jsonplaceholder.typicode.com")
API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "10"))
RESPONSE_TIME_THRESHOLD_MS: float = float(os.getenv("RESPONSE_TIME_THRESHOLD_MS", "2000"))


# ---------------------------------------------------------------------------
# API Client fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def api_client() -> APIClient:
    """Session-scoped API client shared across all tests.

    Using session scope means one requests.Session is opened and reused for
    all tests, which mirrors production behaviour (persistent connections)
    and keeps the suite fast.

    Yields:
        Configured APIClient instance.
    """
    client = APIClient(base_url=BASE_URL, timeout=API_TIMEOUT)
    logger.info("APIClient created — base_url=%s", BASE_URL)
    yield client
    client.close()
    logger.info("APIClient session closed.")


@pytest.fixture(scope="session")
def response_time_threshold() -> float:
    """Return the maximum acceptable API response time in milliseconds.

    Centralised here so tests don't hard-code the threshold, and CI can
    tighten or relax it via the RESPONSE_TIME_THRESHOLD_MS env variable.

    Returns:
        Float millisecond threshold.
    """
    return RESPONSE_TIME_THRESHOLD_MS


# ---------------------------------------------------------------------------
# Test data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_post_payload() -> dict:
    """Return a valid POST /posts request body.

    Function scope (default) so each test that uses it gets a fresh copy —
    prevents one test mutating the dict and affecting another.

    Returns:
        dict with userId, title, and body keys.
    """
    return {
        "userId": 1,
        "title": "Test post title",
        "body": "Test post body content for automated test.",
    }


@pytest.fixture
def sample_user_payload() -> dict:
    """Return a minimal valid user payload for mutation tests.

    Returns:
        dict with name, username, and email keys.
    """
    return {
        "name": "QA Test User",
        "username": "qa_test_user",
        "email": "qa@example.com",
    }


@pytest.fixture
def sample_comment_payload() -> dict:
    """Return a valid POST /comments request body.

    Returns:
        dict with postId, name, email, and body keys.
    """
    return {
        "postId": 1,
        "name": "Automated test comment",
        "email": "tester@example.com",
        "body": "This comment was created by the automated test suite.",
    }


# ---------------------------------------------------------------------------
# Selenium WebDriver fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def chrome_driver():
    """Module-scoped headless Chrome WebDriver.

    Using module scope balances isolation (one driver per test file) and
    speed (no browser launch/teardown for each individual test).

    Yields:
        selenium.webdriver.Chrome instance in headless mode.
    """
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(5)

    logger.info("Chrome WebDriver started (headless).")
    yield driver

    driver.quit()
    logger.info("Chrome WebDriver quit.")


# ---------------------------------------------------------------------------
# pytest hooks
# ---------------------------------------------------------------------------

def pytest_configure(config):
    """Ensure the reports/ directory exists before pytest tries to write the HTML report."""
    import pathlib
    pathlib.Path("reports").mkdir(exist_ok=True)
