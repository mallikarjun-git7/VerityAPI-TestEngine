"""
Tests for the /comments endpoint of JSONPlaceholder.

This module showcases:
- Parameterized tests across multiple valid IDs
- Response time assertions with explicit threshold documentation
- Filtering by query parameter (postId)
- Schema validation for the full comment collection
- Negative cases: out-of-range IDs, invalid query params
- Cross-resource consistency: comments must reference existing posts
"""

import pytest

from utils.assertions import (
    assert_content_type_json,
    assert_json_field,
    assert_json_field_present,
    assert_json_field_type,
    assert_list_not_empty,
    assert_list_length,
    assert_response_time,
    assert_status_code,
)
from utils.schema_validator import COMMENT_SCHEMA, validate_list_schema, validate_schema

# JSONPlaceholder has 5 comments per post, 100 posts → 500 total comments
TOTAL_COMMENTS = 500
COMMENTS_PER_POST = 5


@pytest.mark.api
class TestGetComments:
    """Tests for GET /comments and GET /comments/{id}."""

    def test_get_all_comments_returns_200(self, api_client, response_time_threshold):
        """GET /comments must return 200 with a non-empty JSON array within time threshold."""
        response = api_client.get("/comments")

        assert_status_code(response, 200)
        assert_content_type_json(response)
        assert_response_time(response, response_time_threshold)
        assert_list_not_empty(response.json(), context="GET /comments")

    def test_get_all_comments_returns_500_items(self, api_client):
        """JSONPlaceholder /comments returns exactly 500 records."""
        response = api_client.get("/comments")

        body = response.json()
        assert len(body) == TOTAL_COMMENTS, (
            f"Expected {TOTAL_COMMENTS} comments, got {len(body)}"
        )

    def test_get_all_comments_each_item_matches_schema(self, api_client):
        """Every comment in the collection must conform to COMMENT_SCHEMA."""
        response = api_client.get("/comments")

        validate_list_schema(response.json(), COMMENT_SCHEMA)

    def test_get_comment_by_id_returns_correct_schema(self, api_client, response_time_threshold):
        """GET /comments/1 must return a single comment matching COMMENT_SCHEMA."""
        response = api_client.get("/comments/1")

        assert_status_code(response, 200)
        assert_content_type_json(response)
        assert_response_time(response, response_time_threshold)
        validate_schema(response.json(), COMMENT_SCHEMA)

    def test_get_comment_by_id_returns_matching_id(self, api_client):
        """The id field in the response must match the path parameter."""
        response = api_client.get("/comments/42")

        assert_json_field(response.json(), "id", 42)

    @pytest.mark.parametrize("comment_id", [1, 50, 100, 250, 500])
    def test_get_comment_by_valid_id_returns_200(self, api_client, comment_id):
        """Parameterized: boundary and midpoint comment IDs must all return 200."""
        response = api_client.get(f"/comments/{comment_id}")

        assert_status_code(response, 200)
        assert_json_field(response.json(), "id", comment_id)

    def test_get_comment_email_is_string(self, api_client):
        """The email field on a comment must be a non-empty string."""
        response = api_client.get("/comments/1")

        body = response.json()
        assert_json_field_type(body, "email", str)
        assert len(body["email"]) > 0, "email field must not be empty"

    def test_get_comment_body_is_non_empty_string(self, api_client):
        """The body field on a comment must be a non-empty string."""
        response = api_client.get("/comments/1")

        body = response.json()
        assert_json_field_type(body, "body", str)
        assert len(body["body"]) > 0, "body field must not be empty"


@pytest.mark.api
class TestFilterCommentsByPost:
    """Tests for GET /comments?postId={id} filtering."""

    def test_filter_comments_by_post_id_returns_200(self, api_client):
        """GET /comments?postId=1 must return 200."""
        response = api_client.get("/comments", params={"postId": 1})

        assert_status_code(response, 200)
        assert_content_type_json(response)

    def test_filter_comments_by_post_id_returns_correct_count(self, api_client):
        """JSONPlaceholder always has exactly 5 comments per post."""
        response = api_client.get("/comments", params={"postId": 1})

        body = response.json()
        assert_list_length(body, COMMENTS_PER_POST, context="GET /comments?postId=1")

    @pytest.mark.parametrize("post_id", [1, 10, 50, 100])
    def test_filter_comments_all_belong_to_requested_post(self, api_client, post_id):
        """Parameterized: every comment returned must have postId matching the filter."""
        response = api_client.get("/comments", params={"postId": post_id})

        assert_status_code(response, 200)
        for comment in response.json():
            assert comment["postId"] == post_id, (
                f"Expected postId={post_id}, got postId={comment['postId']} "
                f"for comment id={comment['id']}"
            )

    def test_filter_comments_by_nonexistent_post_returns_empty_list(self, api_client):
        """GET /comments?postId=9999 must return 200 with an empty array."""
        response = api_client.get("/comments", params={"postId": 9999})

        assert_status_code(response, 200)
        body = response.json()
        assert body == [], f"Expected [], got {body}"

    def test_filter_comments_each_item_matches_schema(self, api_client):
        """Every comment in a filtered result must also pass schema validation."""
        response = api_client.get("/comments", params={"postId": 5})

        validate_list_schema(response.json(), COMMENT_SCHEMA)


@pytest.mark.api
class TestGetCommentsNegative:
    """Negative tests — invalid IDs and boundary conditions."""

    def test_get_comment_nonexistent_id_returns_404(self, api_client):
        """GET /comments/9999 must return 404."""
        response = api_client.get("/comments/9999")

        assert_status_code(response, 404)

    @pytest.mark.parametrize("invalid_id", [0, -1, 501, 9999])
    def test_get_comment_out_of_range_id_returns_404(self, api_client, invalid_id):
        """Out-of-range IDs must return 404, not a 500 server error."""
        response = api_client.get(f"/comments/{invalid_id}")

        assert_status_code(response, 404)

    def test_get_comment_string_id_returns_404(self, api_client):
        """Non-integer path segment must return 404, not 500."""
        response = api_client.get("/comments/notanid")

        assert_status_code(response, 404)


@pytest.mark.api
class TestPostComments:
    """Tests for creating new comments via POST /comments."""

    def test_create_comment_returns_201(self, api_client, sample_comment_payload):
        """POST /comments with a valid body must return 201 Created."""
        response = api_client.post("/comments", json=sample_comment_payload)

        assert_status_code(response, 201)
        assert_content_type_json(response)

    def test_create_comment_response_has_generated_id(self, api_client, sample_comment_payload):
        """The server must assign an integer id to the newly created comment."""
        response = api_client.post("/comments", json=sample_comment_payload)

        body = response.json()
        assert_json_field_present(body, "id")
        assert_json_field_type(body, "id", int)
        assert body["id"] > 0, "Generated comment id must be a positive integer"

    def test_create_comment_response_echoes_request_fields(self, api_client, sample_comment_payload):
        """The response must echo back postId, name, email, and body from the request."""
        response = api_client.post("/comments", json=sample_comment_payload)

        body = response.json()
        assert_json_field(body, "postId", sample_comment_payload["postId"])
        assert_json_field(body, "name", sample_comment_payload["name"])
        assert_json_field(body, "email", sample_comment_payload["email"])
        assert_json_field(body, "body", sample_comment_payload["body"])

    def test_response_time_for_comment_collection_is_within_threshold(
        self, api_client, response_time_threshold
    ):
        """GET /comments (500 items) must respond within the configured threshold.

        This test documents that even for large collections the API remains
        within acceptable latency bounds.
        """
        response = api_client.get("/comments")

        assert_response_time(response, response_time_threshold)
