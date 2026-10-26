"""
Reusable custom assertion helpers.

These helpers wrap raw assert statements with clear, descriptive error
messages so that test failures point directly at the problem without
requiring the reader to decode raw values.

Design rules:
- Every helper raises AssertionError (compatible with pytest)
- Every error message states what was expected AND what was received
- Helpers stay generic — no business logic, no schema knowledge
"""

from requests import Response


# ---------------------------------------------------------------------------
# HTTP response assertions
# ---------------------------------------------------------------------------

def assert_status_code(response: Response, expected: int) -> None:
    """Assert the response HTTP status code equals *expected*.

    Args:
        response: The requests.Response object.
        expected: Expected HTTP status code (e.g. 200, 201, 404).
    """
    actual = response.status_code
    assert actual == expected, (
        f"Expected status {expected}, got {actual}.\n"
        f"URL: {response.url}\n"
        f"Body: {response.text[:500]}"
    )


def assert_response_time(response: Response, max_ms: float) -> None:
    """Assert the response was received within *max_ms* milliseconds.

    Uses the `.elapsed_ms` attribute attached by APIClient. Falls back to
    requests' built-in `.elapsed` if the custom attribute is missing (e.g.
    when using requests directly in edge-case tests).

    Args:
        response: The requests.Response object.
        max_ms: Maximum acceptable response time in milliseconds.
    """
    elapsed = getattr(response, "elapsed_ms", None)
    if elapsed is None:
        elapsed = response.elapsed.total_seconds() * 1000

    assert elapsed <= max_ms, (
        f"Response time {elapsed:.0f} ms exceeded threshold of {max_ms} ms.\n"
        f"URL: {response.url}"
    )


def assert_content_type_json(response: Response) -> None:
    """Assert the response Content-Type header indicates JSON.

    Args:
        response: The requests.Response object.
    """
    content_type = response.headers.get("Content-Type", "")
    assert "application/json" in content_type, (
        f"Expected Content-Type 'application/json', got '{content_type}'.\n"
        f"URL: {response.url}"
    )


# ---------------------------------------------------------------------------
# JSON body assertions
# ---------------------------------------------------------------------------

def assert_json_field(body: dict, field: str, expected_value) -> None:
    """Assert a top-level JSON field equals *expected_value*.

    Args:
        body: Parsed JSON response body.
        field: Key to look up in *body*.
        expected_value: Value the field must equal.
    """
    assert field in body, f"Field '{field}' missing from response body: {body}"
    actual = body[field]
    assert actual == expected_value, (
        f"Field '{field}': expected {expected_value!r}, got {actual!r}"
    )


def assert_json_field_present(body: dict, *fields: str) -> None:
    """Assert all given field names exist in *body* (values may be any type).

    Args:
        body: Parsed JSON response body.
        *fields: One or more field names that must be present.
    """
    missing = [f for f in fields if f not in body]
    assert not missing, (
        f"Missing required fields in response body: {missing}\n"
        f"Present keys: {list(body.keys())}"
    )


def assert_json_field_type(body: dict, field: str, expected_type: type) -> None:
    """Assert a JSON field exists and its value is an instance of *expected_type*.

    Args:
        body: Parsed JSON response body.
        field: Key to look up in *body*.
        expected_type: Python type (e.g. int, str, list).
    """
    assert field in body, f"Field '{field}' missing from response body."
    actual_type = type(body[field])
    assert isinstance(body[field], expected_type), (
        f"Field '{field}': expected type {expected_type.__name__}, got {actual_type.__name__}"
    )


def assert_list_not_empty(body: list, context: str = "response") -> None:
    """Assert *body* is a non-empty list.

    Args:
        body: The parsed JSON body, expected to be a list.
        context: Human-readable label used in the error message.
    """
    assert isinstance(body, list), f"Expected a list for {context}, got {type(body).__name__}"
    assert len(body) > 0, f"Expected a non-empty list for {context}, but got []"


def assert_list_length(body: list, expected_length: int, context: str = "response") -> None:
    """Assert *body* is a list with exactly *expected_length* items.

    Args:
        body: The parsed JSON body, expected to be a list.
        expected_length: Exact number of items expected.
        context: Human-readable label used in the error message.
    """
    assert isinstance(body, list), f"Expected a list for {context}, got {type(body).__name__}"
    actual = len(body)
    assert actual == expected_length, (
        f"{context}: expected {expected_length} items, got {actual}"
    )
