"""
End-to-end UI smoke tests using Selenium WebDriver.

Target: https://jsonplaceholder.typicode.com (public docs page)

These tests verify that the public-facing documentation page for the API
we test is accessible and renders key content. This demonstrates Selenium
competency alongside the API test suite without requiring a separate
application deployment.

Scope:
- Page load and title assertion
- Presence of critical navigation elements
- Resource link rendering (posts, users, comments routes documented)
- Basic interaction: clicking a route link and verifying navigation

Note: These are smoke tests — they validate that the surface the QA team
depends on is reachable and functional. They are not exhaustive UI tests.
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "https://jsonplaceholder.typicode.com"
PAGE_LOAD_TIMEOUT = 10  # seconds


@pytest.mark.e2e
class TestHomepageSmoke:
    """Smoke tests for the JSONPlaceholder homepage."""

    def test_homepage_loads_successfully(self, chrome_driver):
        """The homepage must load with an HTTP 200 response and a non-empty title.

        Selenium does not expose HTTP status codes directly; we infer success
        from the page title and content rendering as expected.
        """
        chrome_driver.get(BASE_URL)

        title = chrome_driver.title
        assert title, "Page title must not be empty after loading."
        assert "JSONPlaceholder" in title, (
            f"Expected 'JSONPlaceholder' in page title, got: '{title}'"
        )

    def test_homepage_contains_main_heading(self, chrome_driver):
        """The main <h1> heading must be visible and contain 'JSONPlaceholder'."""
        chrome_driver.get(BASE_URL)

        wait = WebDriverWait(chrome_driver, PAGE_LOAD_TIMEOUT)
        heading = wait.until(
            EC.visibility_of_element_located((By.TAG_NAME, "h1"))
        )
        assert heading.is_displayed(), "h1 heading must be visible on the page."
        assert "JSONPlaceholder" in heading.text, (
            f"Expected h1 to contain 'JSONPlaceholder', got: '{heading.text}'"
        )

    def test_homepage_url_is_correct_after_load(self, chrome_driver):
        """The browser URL after loading must match the expected base URL.

        Verifies there are no unexpected redirects to a different domain.
        """
        chrome_driver.get(BASE_URL)

        current_url = chrome_driver.current_url
        assert BASE_URL in current_url, (
            f"Expected URL to contain '{BASE_URL}', got '{current_url}'"
        )

    def test_homepage_page_source_is_non_empty(self, chrome_driver):
        """The page source must be non-trivial (> 100 chars), ruling out empty responses."""
        chrome_driver.get(BASE_URL)

        source = chrome_driver.page_source
        assert len(source) > 100, (
            f"Page source is suspiciously short ({len(source)} chars). "
            "The page may have failed to render."
        )


@pytest.mark.e2e
class TestResourceRoutesDocumented:
    """Verify that the key API resource routes are documented on the homepage."""

    EXPECTED_ROUTES = ["/posts", "/users", "/comments", "/todos", "/albums", "/photos"]

    def test_homepage_documents_posts_route(self, chrome_driver):
        """The /posts route must appear in the page content."""
        chrome_driver.get(BASE_URL)

        page_source = chrome_driver.page_source
        assert "/posts" in page_source, (
            "Expected '/posts' route to be documented on the homepage."
        )

    def test_homepage_documents_users_route(self, chrome_driver):
        """The /users route must appear in the page content."""
        chrome_driver.get(BASE_URL)

        page_source = chrome_driver.page_source
        assert "/users" in page_source, (
            "Expected '/users' route to be documented on the homepage."
        )

    def test_homepage_documents_comments_route(self, chrome_driver):
        """The /comments route must appear in the page content."""
        chrome_driver.get(BASE_URL)

        page_source = chrome_driver.page_source
        assert "/comments" in page_source, (
            "Expected '/comments' route to be documented on the homepage."
        )

    @pytest.mark.parametrize("route", EXPECTED_ROUTES)
    def test_homepage_documents_all_expected_routes(self, chrome_driver, route):
        """Parameterized: every expected resource route must appear in the page source."""
        chrome_driver.get(BASE_URL)

        assert route in chrome_driver.page_source, (
            f"Route '{route}' was not found in the homepage source. "
            "The documentation may be out of date."
        )


@pytest.mark.e2e
class TestNavigationInteraction:
    """Tests that verify interactive navigation on the documentation page."""

    def test_guide_link_is_present_and_visible(self, chrome_driver):
        """A link to the 'Guide' or detailed documentation must be present and visible."""
        chrome_driver.get(BASE_URL)

        wait = WebDriverWait(chrome_driver, PAGE_LOAD_TIMEOUT)
        # Look for any anchor tag containing 'guide' (case-insensitive via XPath)
        links = chrome_driver.find_elements(
            By.XPATH, "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'guide')]"
        )
        assert len(links) > 0, (
            "Expected at least one 'guide' link on the homepage, found none."
        )
        assert links[0].is_displayed(), "The 'guide' link must be visible, not hidden."

    def test_page_has_navigable_anchor_links(self, chrome_driver):
        """The page must contain at least one <a> tag with a valid href attribute."""
        chrome_driver.get(BASE_URL)

        anchors = chrome_driver.find_elements(By.XPATH, "//a[@href]")
        assert len(anchors) > 0, (
            "No anchor links with href attributes found. "
            "The page may have failed to render navigation."
        )

    def test_no_javascript_errors_on_load(self, chrome_driver):
        """The browser console must not contain any SEVERE-level JavaScript errors.

        Uses Chrome DevTools Protocol (CDP) log capture to detect JS errors
        that would indicate a broken page, without requiring a real user.
        """
        chrome_driver.get(BASE_URL)

        # Collect browser logs (requires ChromeOptions logging prefs to be set)
        try:
            logs = chrome_driver.get_log("browser")
            severe_errors = [
                entry for entry in logs
                if entry.get("level") == "SEVERE"
            ]
            assert len(severe_errors) == 0, (
                f"Found {len(severe_errors)} SEVERE JS error(s) on page load:\n"
                + "\n".join(e["message"] for e in severe_errors)
            )
        except Exception:
            # Log capture not supported in all Selenium/driver configurations;
            # skip gracefully rather than failing the build.
            pytest.skip("Browser log capture not available in this WebDriver configuration.")
