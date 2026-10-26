"""
JSON Schema validation utility.

Centralizes all schema definitions and validation logic so that:
- Test files stay focused on assertions, not schema boilerplate
- Schema changes only need to happen in one place
- Validation errors produce clear, actionable messages
"""

import jsonschema
from jsonschema import ValidationError, validate


# ---------------------------------------------------------------------------
# Schema definitions
# ---------------------------------------------------------------------------

POST_SCHEMA: dict = {
    "type": "object",
    "required": ["userId", "id", "title", "body"],
    "properties": {
        "userId": {"type": "integer", "minimum": 1},
        "id":     {"type": "integer", "minimum": 1},
        "title":  {"type": "string", "minLength": 1},
        "body":   {"type": "string", "minLength": 1},
    },
    "additionalProperties": False,
}

USER_SCHEMA: dict = {
    "type": "object",
    "required": ["id", "name", "username", "email", "address", "phone", "website", "company"],
    "properties": {
        "id":       {"type": "integer", "minimum": 1},
        "name":     {"type": "string", "minLength": 1},
        "username": {"type": "string", "minLength": 1},
        "email":    {"type": "string", "format": "email"},
        "address": {
            "type": "object",
            "required": ["street", "suite", "city", "zipcode", "geo"],
            "properties": {
                "street":  {"type": "string"},
                "suite":   {"type": "string"},
                "city":    {"type": "string"},
                "zipcode": {"type": "string"},
                "geo": {
                    "type": "object",
                    "required": ["lat", "lng"],
                    "properties": {
                        "lat": {"type": "string"},
                        "lng": {"type": "string"},
                    },
                },
            },
        },
        "phone":   {"type": "string"},
        "website": {"type": "string"},
        "company": {
            "type": "object",
            "required": ["name", "catchPhrase", "bs"],
            "properties": {
                "name":        {"type": "string"},
                "catchPhrase": {"type": "string"},
                "bs":          {"type": "string"},
            },
        },
    },
    "additionalProperties": False,
}

COMMENT_SCHEMA: dict = {
    "type": "object",
    "required": ["postId", "id", "name", "email", "body"],
    "properties": {
        "postId": {"type": "integer", "minimum": 1},
        "id":     {"type": "integer", "minimum": 1},
        "name":   {"type": "string", "minLength": 1},
        "email":  {"type": "string"},
        "body":   {"type": "string", "minLength": 1},
    },
    "additionalProperties": False,
}

# Maps resource name -> schema for convenience
SCHEMAS: dict[str, dict] = {
    "post":    POST_SCHEMA,
    "user":    USER_SCHEMA,
    "comment": COMMENT_SCHEMA,
}


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_schema(instance: dict, schema: dict) -> None:
    """Assert that *instance* conforms to *schema*.

    Raises:
        AssertionError: With a human-readable message listing the first
            validation failure found by jsonschema.
    """
    try:
        validate(instance=instance, schema=schema)
    except ValidationError as exc:
        raise AssertionError(
            f"Schema validation failed at '{'.'.join(str(p) for p in exc.absolute_path)}': "
            f"{exc.message}"
        ) from exc


def validate_list_schema(instances: list[dict], schema: dict) -> None:
    """Assert every item in *instances* conforms to *schema*.

    Args:
        instances: List of response objects to validate.
        schema: JSON Schema dict each item must satisfy.

    Raises:
        AssertionError: On the first item that fails validation, with its
            index included in the error message.
    """
    for idx, item in enumerate(instances):
        try:
            validate(instance=item, schema=schema)
        except ValidationError as exc:
            raise AssertionError(
                f"Schema validation failed for item [{idx}] "
                f"at '{'.'.join(str(p) for p in exc.absolute_path)}': "
                f"{exc.message}"
            ) from exc


def validate_resource(resource_name: str, instance: dict) -> None:
    """Validate *instance* against the named schema from the SCHEMAS registry.

    Args:
        resource_name: One of "post", "user", "comment".
        instance: Response body dict to validate.

    Raises:
        KeyError: If *resource_name* is not registered.
        AssertionError: If schema validation fails.
    """
    schema = SCHEMAS[resource_name]
    validate_schema(instance, schema)
