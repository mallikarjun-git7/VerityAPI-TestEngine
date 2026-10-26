"""
Tests for the /users endpoint of JSONPlaceholder.

Coverage:
- GET collection and individual resource
- Schema validation including deeply nested address/geo/company objects
- Edge cases: invalid IDs, boundary values, non-integer path segments
- Field-level type assertions for critical fields
- Response time validation
"""

import pytest

from utils.assertions import (
    assert_content_type_json,
    assert_json_field,
    assert_json_field_present,
    assert_json_field_type,
    assert_list_not_empty,
    assert_response_time,
    assert_status_code,
)
from utils.schema_validator import USER_SCHEMA, validate_list_schema, validate_schema


@pytest.mark.api
class TestGetUsers:
    """Tests for GET /users and GET /users/{id}."""

    def test_get_all_users_returns_200(self, api_client, response_time_threshold):
        """GET /users must return 200 with a non-empty JSON array within time threshold."""
        response = api_client.get("/users")

        assert_status_code(response, 200)
        assert_content_type_json(response)
        assert_response_time(response, response_time_threshold)
        assert_list_not_empty(response.json(), context="GET /users")

    def test_get_all_users_returns_10_items(self, api_client):
        """JSONPlaceholder /users always returns exactly 10 records."""
        response = api_client.get("/users")

        body = response.json()
        assert len(body) == 10, f"Expected 10 users, got {len(body)}"

    def test_get_all_users_each_item_matches_schema(self, api_client):
        """Every user object in the collection must conform to USER_SCHEMA."""
        response = api_client.get("/users")

        validate_list_schema(response.json(), USER_SCHEMA)

    def test_get_user_by_id_returns_correct_schema(self, api_client, response_time_threshold):
        """GET /users/1 must return a single user matching USER_SCHEMA."""
        response = api_client.get("/users/1")

        assert_status_code(response, 200)
        assert_content_type_json(response)
        assert_response_time(response, response_time_threshold)
        validate_schema(response.json(), USER_SCHEMA)

    def test_get_user_by_id_returns_correct_id(self, api_client):
        """The id field in the response must match the id in the path."""
        response = api_client.get("/users/3")

        assert_json_field(response.json(), "id", 3)

    @pytest.mark.parametrize("user_id", [1, 3, 5, 7, 10])
    def test_get_user_by_valid_id_returns_200(self, api_client, user_id):
        """Parameterized: a sample of valid user IDs must all return 200."""
        response = api_client.get(f"/users/{user_id}")

        assert_status_code(response, 200)
        assert_json_field(response.json(), "id", user_id)

    def test_get_user_has_required_contact_fields(self, api_client):
        """Each user record must include email, phone, and website fields."""
        response = api_client.get("/users/1")

        body = response.json()
        assert_json_field_present(body, "email", "phone", "website")

    def test_get_user_email_is_string(self, api_client):
        """The email field must be a string (type check, not format check)."""
        response = api_client.get("/users/1")

        assert_json_field_type(response.json(), "email", str)

    def test_get_user_has_nested_address(self, api_client):
        """The address field must be a dict containing city and zipcode."""
        response = api_client.get("/users/1")

        body = response.json()
        assert_json_field_present(body, "address")
        address = body["address"]
        assert isinstance(address, dict), f"Expected address to be a dict, got {type(address)}"
        assert_json_field_present(address, "city", "zipcode", "street", "suite")

    def test_get_user_address_has_geo_coordinates(self, api_client):
        """address.geo must contain lat and lng string fields."""
        response = api_client.get("/users/1")

        geo = response.json()["address"]["geo"]
        assert isinstance(geo, dict), f"Expected geo to be a dict, got {type(geo)}"
        assert_json_field_present(geo, "lat", "lng")
        assert_json_field_type(geo, "lat", str)
        assert_json_field_type(geo, "lng", str)

    def test_get_user_has_nested_company(self, api_client):
        """The company field must be a dict with name, catchPhrase, and bs."""
        response = api_client.get("/users/1")

        body = response.json()
        assert_json_field_present(body, "company")
        company = body["company"]
        assert isinstance(company, dict), f"Expected company to be a dict, got {type(company)}"
        assert_json_field_present(company, "name", "catchPhrase", "bs")


@pytest.mark.api
class TestGetUsersNegative:
    """Negative tests for /users — invalid inputs and boundary values."""

    def test_get_user_nonexistent_id_returns_404(self, api_client):
        """GET /users/9999 must return 404 — resource does not exist."""
        response = api_client.get("/users/9999")

        assert_status_code(response, 404)

    @pytest.mark.parametrize("invalid_id", [0, -1, 11, 100, 9999])
    def test_get_user_out_of_range_id_returns_404(self, api_client, invalid_id):
        """Out-of-range IDs (0, negative, or > 10) must return 404, not 500."""
        response = api_client.get(f"/users/{invalid_id}")

        assert_status_code(response, 404)

    def test_get_user_string_id_returns_404(self, api_client):
        """Non-integer path segment (e.g., 'abc') must return 404, not 500."""
        response = api_client.get("/users/abc")

        assert_status_code(response, 404)

    def test_get_user_float_id_returns_404(self, api_client):
        """Float path segment (e.g., '1.5') must return 404, not 500."""
        response = api_client.get("/users/1.5")

        assert_status_code(response, 404)


@pytest.mark.api
class TestUsersRelationships:
    """Tests that validate the relationship between users and their posts."""

    def test_get_posts_for_user_returns_non_empty_list(self, api_client):
        """GET /users/1/posts must return a non-empty list of posts."""
        response = api_client.get("/users/1/posts")

        assert_status_code(response, 200)
        assert_list_not_empty(response.json(), context="GET /users/1/posts")

    def test_all_posts_for_user_belong_to_that_user(self, api_client):
        """Every post returned by /users/1/posts must have userId == 1."""
        response = api_client.get("/users/1/posts")

        for post in response.json():
            assert post["userId"] == 1, (
                f"Post id={post['id']} has userId={post['userId']}, expected userId=1"
            )

    def test_get_todos_for_user_returns_non_empty_list(self, api_client):
        """GET /users/1/todos must return a non-empty list of todo items."""
        response = api_client.get("/users/1/todos")

        assert_status_code(response, 200)
        assert_list_not_empty(response.json(), context="GET /users/1/todos")

    def test_todos_for_nonexistent_user_returns_empty_list(self, api_client):
        """GET /users/9999/todos must return 200 with an empty array."""
        response = api_client.get("/users/9999/todos")

        assert_status_code(response, 200)
        body = response.json()
        assert body == [], f"Expected empty list for unknown user, got {body}"
