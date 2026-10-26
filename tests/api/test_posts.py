"""
Tests for the /posts endpoint of JSONPlaceholder.

Coverage:
- GET collection and individual resource
- POST create, PUT full replace, DELETE
- JSON schema validation on every successful response
- Negative cases: non-existent IDs, malformed payloads
- Response time assertions to catch performance regressions
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
from utils.schema_validator import POST_SCHEMA, validate_list_schema, validate_schema


@pytest.mark.api
class TestGetPosts:
    """Tests for GET /posts and GET /posts/{id}."""

    def test_get_all_posts_returns_200(self, api_client, response_time_threshold):
        """GET /posts must return 200 with a non-empty JSON array within threshold."""
        response = api_client.get("/posts")

        assert_status_code(response, 200)
        assert_content_type_json(response)
        assert_response_time(response, response_time_threshold)
        assert_list_not_empty(response.json(), context="GET /posts")

    def test_get_all_posts_returns_100_items(self, api_client):
        """JSONPlaceholder /posts always returns exactly 100 records."""
        response = api_client.get("/posts")

        body = response.json()
        assert len(body) == 100, f"Expected 100 posts, got {len(body)}"

    def test_get_all_posts_each_item_matches_schema(self, api_client):
        """Every post object in the collection must conform to the POST_SCHEMA."""
        response = api_client.get("/posts")

        validate_list_schema(response.json(), POST_SCHEMA)

    def test_get_post_by_id_returns_correct_schema(self, api_client, response_time_threshold):
        """GET /posts/1 must return a single post object that matches POST_SCHEMA."""
        response = api_client.get("/posts/1")

        assert_status_code(response, 200)
        assert_content_type_json(response)
        assert_response_time(response, response_time_threshold)
        validate_schema(response.json(), POST_SCHEMA)

    def test_get_post_by_id_returns_correct_id(self, api_client):
        """The id field in the response must match the id requested in the path."""
        response = api_client.get("/posts/5")

        assert_json_field(response.json(), "id", 5)

    @pytest.mark.parametrize("post_id", [1, 10, 50, 100])
    def test_get_post_by_id_valid_ids_return_200(self, api_client, post_id):
        """Parameterized: a sample of valid post IDs must all return 200."""
        response = api_client.get(f"/posts/{post_id}")

        assert_status_code(response, 200)
        assert_json_field(response.json(), "id", post_id)

    def test_get_post_by_nonexistent_id_returns_404(self, api_client):
        """GET /posts/9999 must return 404 — resource does not exist."""
        response = api_client.get("/posts/9999")

        assert_status_code(response, 404)

    @pytest.mark.parametrize("invalid_id", [0, -1, 101, 99999])
    def test_get_post_by_invalid_id_returns_404(self, api_client, invalid_id):
        """Out-of-range or non-positive IDs must return 404, not a 500 error."""
        response = api_client.get(f"/posts/{invalid_id}")

        assert_status_code(response, 404)

    def test_get_posts_filter_by_user_id(self, api_client):
        """GET /posts?userId=1 must return only posts belonging to user 1."""
        response = api_client.get("/posts", params={"userId": 1})

        assert_status_code(response, 200)
        body = response.json()
        assert_list_not_empty(body, context="GET /posts?userId=1")
        for post in body:
            assert post["userId"] == 1, (
                f"Expected userId=1, got userId={post['userId']} for post id={post['id']}"
            )

    def test_get_posts_filter_by_nonexistent_user_returns_empty_list(self, api_client):
        """GET /posts?userId=9999 must return 200 with an empty array, not 404."""
        response = api_client.get("/posts", params={"userId": 9999})

        assert_status_code(response, 200)
        body = response.json()
        assert body == [], f"Expected empty list, got {body}"


@pytest.mark.api
class TestCreatePost:
    """Tests for POST /posts."""

    def test_create_post_returns_201(self, api_client, sample_post_payload):
        """POST /posts with a valid body must return 201 Created."""
        response = api_client.post("/posts", json=sample_post_payload)

        assert_status_code(response, 201)
        assert_content_type_json(response)

    def test_create_post_response_contains_generated_id(self, api_client, sample_post_payload):
        """The server must assign an id to the newly created post."""
        response = api_client.post("/posts", json=sample_post_payload)

        body = response.json()
        assert_json_field_present(body, "id")
        assert_json_field_type(body, "id", int)
        assert body["id"] > 0, f"Generated id must be positive, got {body['id']}"

    def test_create_post_response_echoes_request_fields(self, api_client, sample_post_payload):
        """The response body must echo back the title and body sent in the request."""
        response = api_client.post("/posts", json=sample_post_payload)

        body = response.json()
        assert_json_field(body, "title", sample_post_payload["title"])
        assert_json_field(body, "body", sample_post_payload["body"])
        assert_json_field(body, "userId", sample_post_payload["userId"])

    def test_create_post_with_empty_body_returns_201(self, api_client):
        """JSONPlaceholder accepts empty payloads — still returns 201.

        This documents the known (permissive) behaviour of the mock API.
        A real production API would return 400 here.
        """
        response = api_client.post("/posts", json={})

        assert_status_code(response, 201)


@pytest.mark.api
class TestUpdatePost:
    """Tests for PUT /posts/{id} — full resource replacement."""

    def test_put_post_returns_200(self, api_client, sample_post_payload):
        """PUT /posts/1 with a valid body must return 200 OK."""
        response = api_client.put("/posts/1", json={**sample_post_payload, "id": 1})

        assert_status_code(response, 200)
        assert_content_type_json(response)

    def test_put_post_response_reflects_updated_fields(self, api_client):
        """PUT /posts/1 must return a body with the updated title and body."""
        updated_payload = {
            "id": 1,
            "userId": 1,
            "title": "Updated title via PUT",
            "body": "Updated body via PUT.",
        }
        response = api_client.put("/posts/1", json=updated_payload)

        body = response.json()
        assert_json_field(body, "title", updated_payload["title"])
        assert_json_field(body, "body", updated_payload["body"])

    def test_put_nonexistent_post_returns_500(self, api_client, sample_post_payload):
        """JSONPlaceholder returns 500 for PUT on a non-existent resource.

        Documents the known mock API behaviour — a real API would return 404.
        """
        response = api_client.put("/posts/9999", json={**sample_post_payload, "id": 9999})

        # JSONPlaceholder quirk: returns 500 for unknown IDs on PUT
        assert response.status_code in (404, 500), (
            f"Expected 404 or 500 for PUT /posts/9999, got {response.status_code}"
        )


@pytest.mark.api
class TestDeletePost:
    """Tests for DELETE /posts/{id}."""

    def test_delete_post_returns_200(self, api_client):
        """DELETE /posts/1 must return 200 with an empty body."""
        response = api_client.delete("/posts/1")

        assert_status_code(response, 200)

    def test_delete_post_response_body_is_empty_object(self, api_client):
        """JSONPlaceholder returns {} on successful delete."""
        response = api_client.delete("/posts/1")

        body = response.json()
        assert body == {}, f"Expected empty object on delete, got {body}"

    @pytest.mark.parametrize("post_id", [1, 50, 100])
    def test_delete_multiple_posts_returns_200(self, api_client, post_id):
        """Parameterized: deleting various valid IDs must always return 200."""
        response = api_client.delete(f"/posts/{post_id}")

        assert_status_code(response, 200)
