"""Export the actual installed django-allauth OpenAPI JSON, deterministically.

Run: uv run --locked python tools/export_headless_openapi.py
Check: uv run --locked python tools/export_headless_openapi.py --check
"""
import argparse
import json
import os
import sys
from pathlib import Path

import django
from django.test import Client


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.spec"
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
    if not any("/browser/v1/auth/session" in p for p in paths):
        print("OpenAPI lacks browser session routes", file=sys.stderr)
        return 1

    normalized = json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    path = Path(__file__).resolve().parents[2] / "docs/api/allauth-browser-openapi.json"
    if args.check:
        if not path.is_file() or path.read_text(encoding="utf-8") != normalized:
            print(f"OpenAPI drift detected: {path}", file=sys.stderr)
            return 1
        print(f"OpenAPI matches committed snapshot: {len(paths)} paths")
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(normalized, encoding="utf-8")
    print(f"Exported verified upstream OpenAPI: {len(paths)} paths -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
