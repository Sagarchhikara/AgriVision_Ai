"""
backend/openapi_export.py

Writes the API's OpenAPI schema to a file, for the frontend's type generation
(`npm run gen:api` in frontend/).

Builds the app without running its lifespan, so this needs no checkpoint, no
dataset, and no API keys -- only the backend's Python dependencies. Writes to a
file rather than stdout because app construction logs to stdout.

Usage:
    python -m backend.openapi_export frontend/openapi.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from backend.app import app


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: python -m backend.openapi_export <output.json>")
    output = Path(sys.argv[1])
    output.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote OpenAPI schema to {output}")


if __name__ == "__main__":
    main()
