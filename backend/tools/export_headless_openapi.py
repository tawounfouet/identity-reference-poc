"""Export the actual installed django-allauth OpenAPI JSON, deterministically.

Run: uv run --locked python tools/export_headless_openapi.py
Check: uv run --locked python tools/export_headless_openapi.py --check
"""
import argparse
import difflib
import json
import os
import sys
import uuid
from pathlib import Path

import django
from django.test import Client



def canonicalize_example_uuids(value: object) -> object:
    """Normalize randomly generated UUID4s in upstream example values.

    Preserve equality between repeated references and deterministic numbering
    for distinct examples. All non-example schemas and fields are retained.
    """
    mapped: dict[str, str] = {}

    def visit(node: object) -> object:
        if isinstance(node, dict):
            result = {}
            for key, item in sorted(node.items()):
                if key in {"id", "example"} and isinstance(item, str):
                    try:
                        value_uuid = uuid.UUID(item)
                    except ValueError:
                        pass
                    else:
                        if value_uuid.version == 4:
                            if item not in mapped:
                                mapped[item] = (
                                    f"00000000-0000-4000-8000-{len(mapped) + 1:012x}"
                                )
                            result[key] = mapped[item]
                            continue
                result[key] = visit(item)
            return result
        if isinstance(node, list):
            return [visit(item) for item in node]
        return node

    return visit(value)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.spec"
    # The script runs inside backend/tools; add backend/ to the import path.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    django.setup()
    response = Client().get("/_allauth/openapi.json")
    if response.status_code != 200:
        print(f"Expected HTTP 200, got {response.status_code}", file=sys.stderr)
        return 1

    try:
        payload = json.loads(response.content)
    except json.JSONDecodeError as exc:
        print(f"Invalid upstream OpenAPI JSON: {exc}", file=sys.stderr)
        return 1

    paths = payload.get("paths", {})
    if not payload.get("openapi") or not isinstance(paths, dict) or not paths:
        print("Upstream OpenAPI payload is empty or invalid", file=sys.stderr)
        return 1

    # Fail closed if the installed spec does not expose the required browser
    # endpoints, rather than writing an invented/custom substitute.
    if "/_allauth/browser/v1/auth/session" not in paths:
        print("OpenAPI lacks the browser session endpoint", file=sys.stderr)
        return 1
    if any(not path.startswith("/_allauth/browser/v1/") for path in paths):
        print("Non-browser paths found in browser-only snapshot", file=sys.stderr)
        return 1

    normalized_payload = canonicalize_example_uuids(payload)
    normalized = json.dumps(normalized_payload, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    path = Path(__file__).resolve().parents[2] / "docs/api/allauth-browser-openapi.json"
    if args.check:
        if not path.is_file():
            print(f"OpenAPI snapshot missing: {path}", file=sys.stderr)
            return 1
        committed = path.read_text(encoding="utf-8")
        if committed != normalized:
            print(f"OpenAPI drift detected: {path}", file=sys.stderr)
            diff = difflib.unified_diff(
                committed.splitlines(),
                normalized.splitlines(),
                fromfile="committed.json",
                tofile="generated.json",
                lineterm="",
            )
            for index, line in enumerate(diff):
                if index >= 50:
                    print("... diff truncated ...", file=sys.stderr)
                    break
                print(line[:350], file=sys.stderr)
            return 1
        print(f"OpenAPI matches committed snapshot: {len(paths)} paths")
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(normalized, encoding="utf-8")
    print(f"Exported verified upstream OpenAPI: {len(paths)} paths -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
