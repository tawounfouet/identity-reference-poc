"""Headless upstream example normalization is deterministic."""

import copy
import uuid

from tools.export_headless_openapi import canonicalize_example_uuids


def make_doc(user_a: str, user_b: str) -> dict:
    return {
        "components": {
            "examples": {
                "one": {"value": {"id": user_a}},
                "repeated": {"value": {"id": user_a}},
                "other": {"value": {"id": user_b}},
            },
            "schemas": {
                "User": {"properties": {"id": {"type": "string", "example": user_a}}}
            },
        }
    }


def test_example_uuid_canonicalization_is_stable_across_runs():
    first_a, first_b = str(uuid.uuid4()), str(uuid.uuid4())
    second_a, second_b = str(uuid.uuid4()), str(uuid.uuid4())
    original = make_doc(first_a, first_b)
    untouched = copy.deepcopy(original)
    result = canonicalize_example_uuids(original)
    subsequent = canonicalize_example_uuids(make_doc(second_a, second_b))
    assert result == subsequent
    assert original == untouched

    examples = result["components"]["examples"]
    schema = result["components"]["schemas"]["User"]
    assert examples["one"]["value"]["id"] == examples["repeated"]["value"]["id"]
    assert examples["one"]["value"]["id"] != examples["other"]["value"]["id"]
    assert schema["properties"]["id"]["example"] == examples["one"]["value"]["id"]
    assert schema["properties"]["id"]["type"] == "string"


def test_non_uuid_identifiers_not_modified():
    document = {"id": "business-id", "example": "username", "properties": {"id": {"type": "string"}}}
    assert canonicalize_example_uuids(document) == document
