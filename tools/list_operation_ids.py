import argparse
import json
import os
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


def load_schema(schema_path: Path) -> dict:
    text = schema_path.read_text(encoding="utf-8")
    if schema_path.suffix.lower() in {".yml", ".yaml"}:
        if yaml is None:
            raise RuntimeError("PyYAML is required for YAML schemas. Install with: pip install pyyaml")
        return yaml.safe_load(text)
    return json.loads(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="List OpenAPI operationIds and methods/paths")
    parser.add_argument("--all", action="store_true", help="List all endpoints (ignore critical filter)")
    parser.add_argument(
        "--schema",
        type=str,
        default=None,
        help="Path to schema file (defaults to ./schema.yml or ./schema.json)",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=str(Path(__file__).resolve().parents[1] / "operations.txt"),
        help="Output file path (default: operations.txt at repo root)",
    )
    parser.add_argument(
        "--filter",
        action="append",
        default=["/api/auth/token", "/api/auth/token/refresh", "/api/v1/students", "/api/v1/attendance"],
        help="Filter paths that contain this substring (can be used multiple times)",
    )

    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    if args.schema:
        schema_path = Path(args.schema)
    else:
        schema_path = root / "schema.yml"
        if not schema_path.exists():
            schema_path = root / "schema.json"

    spec = load_schema(schema_path)
    paths = spec.get("paths", {})

    lines = []
    for path, ops in paths.items():
        for method, details in ops.items():
            if not isinstance(details, dict):
                continue
            op_id = details.get("operationId", "[NO operationId]")
            if not args.all and args.filter:
                if not any(substr in path for substr in args.filter):
                    continue
            lines.append(f"{op_id} -> {method.upper()} {path}")

    lines.sort()
    out_path = Path(args.out)
    out_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    for line in lines:
        print(line)
    print(f"\nWrote {len(lines)} operationIds to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
