import argparse
import json
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    print("[ERROR] PyYAML is required. Install with: pip install PyYAML", file=sys.stderr)
    raise SystemExit(2)

try:
    from openapi_spec_validator import validate_spec
except Exception:  # pragma: no cover
    print(
        "[ERROR] openapi-spec-validator is required. Install with: pip install openapi-spec-validator",
        file=sys.stderr,
    )
    raise SystemExit(2)


def load_schema(schema_path: Path) -> dict:
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    text = schema_path.read_text(encoding="utf-8")
    if schema_path.suffix.lower() in {".yml", ".yaml"}:
        return yaml.safe_load(text)
    return json.loads(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate OpenAPI schema (YAML or JSON)")
    parser.add_argument(
        "schema",
        nargs="?",
        default=None,
        help="Path to schema file. Defaults to ./schema.yml or ./schema.json",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    schema_path: Path
    if args.schema:
        schema_path = Path(args.schema).resolve()
    else:
        schema_path = (root / "schema.yml") if (root / "schema.yml").exists() else (root / "schema.json")

    print(f"Validating schema: {schema_path}")
    try:
        schema = load_schema(schema_path)
    except Exception as exc:
        print(f"[ERROR] Failed to load schema: {exc}")
        return 2

    try:
        validate_spec(schema)
        print("[OK] OpenAPI schema is valid.")
        return 0
    except Exception as exc:
        print("[FAIL] OpenAPI schema validation errors detected:")
        # openapi-spec-validator raises exceptions that often contain nested messages
        print(f" - {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


