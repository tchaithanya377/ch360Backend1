import sys
import json
from typing import Dict, Any


def load_schema(path: str) -> Dict[str, Any]:
    import yaml  # type: ignore
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main() -> None:
    if len(sys.argv) < 2:
        schema_path = 'schema.yml'
    else:
        schema_path = sys.argv[1]

    schema = load_schema(schema_path)
    paths = schema.get('paths', {}) or {}

    endpoints = []
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}:
                continue
            summary = (op or {}).get('summary') or (op or {}).get('operationId') or ''
            endpoints.append({
                'method': method.upper(),
                'path': path,
                'summary': summary,
            })

    # Sort by path then method for readability
    endpoints.sort(key=lambda e: (e['path'], e['method']))
    for e in endpoints:
        print(f"{e['method']:6} {e['path']}\t{e['summary']}")


if __name__ == '__main__':
    main()


