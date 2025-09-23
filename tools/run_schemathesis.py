#!/usr/bin/env python3
"""
Schemathesis test runner for Django API testing.
Avoids PowerShell command-line length issues by using Python subprocess.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def load_operations(operations_file: Path) -> list:
    """Load operation entries from operations.txt file."""
    if not operations_file.exists():
        return []
    
    entries = []
    with open(operations_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Parse: operationId -> METHOD PATH
            match = re.match(r'^(.+?)\s+->\s+([A-Z]+)\s+(.+)$', line)
            if match:
                op_id, method, path = match.groups()
                if op_id and op_id != "[NO operationId]":
                    entries.append({
                        'id': op_id.strip(),
                        'method': method.strip().upper(),
                        'path': path.strip()
                    })
    
    return entries


def run_schemathesis_batch(schema_path: Path, base_url: str, entries: list, 
                          max_examples: int, workers: int, auth_token: str | None = None) -> int:
    """Run schemathesis on a batch of operations."""
    
    # Check if schemathesis CLI is available
    try:
        subprocess.run(['schemathesis', '--version'], 
                      capture_output=True, check=True)
        cmd = ['schemathesis', 'run']
    except (subprocess.CalledProcessError, FileNotFoundError):
        cmd = ['python', '-m', 'schemathesis.cli', 'run']
    
    # Build include-path regex
    escaped_paths = []
    for entry in entries:
        escaped_path = re.escape(entry['path'])
        # Make the regex more flexible - allow optional trailing slash
        if escaped_path.endswith('/'):
            escaped_path = escaped_path[:-1] + '/?'
        else:
            escaped_path = escaped_path + '/?'
        escaped_paths.append(f"^{escaped_path}$")
    
    path_regex = "|".join(escaped_paths)
    
    # Build command
    args = cmd + [
        '--max-examples', str(max_examples),
        '--workers', str(workers),
        '--include-path', path_regex,
        '--url', base_url,
        str(schema_path)
    ]

    if auth_token:
        args = cmd + [
            '--max-examples', str(max_examples),
            '--workers', str(workers),
            '--include-path', path_regex,
            '--header', f'Authorization: Bearer {auth_token}',
            '--url', base_url,
            str(schema_path)
        ]
    
    print(f"Running: {' '.join(args)}")
    
    try:
        result = subprocess.run(args, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Schemathesis failed with exit code {e.returncode}")
        return e.returncode


def main():
    parser = argparse.ArgumentParser(description='Run Schemathesis tests')
    parser.add_argument('--schema', default='schema.yml', 
                       help='Path to OpenAPI schema file')
    parser.add_argument('--base-url', default='http://127.0.0.1:8000',
                       help='Base URL for API testing')
    parser.add_argument('--operations', default='operations.txt',
                       help='Path to operations file')
    parser.add_argument('--max-examples', type=int, default=5,
                       help='Maximum examples per operation')
    parser.add_argument('--workers', type=int, default=1,
                       help='Number of worker threads')
    parser.add_argument('--max-ops-per-run', type=int, default=20,
                       help='Maximum operations per batch')
    parser.add_argument('--generate-ops', action='store_true',
                       help='Generate operations file if missing')
    parser.add_argument('--auth-token', default=None,
                       help='Bearer token for Authorization header')
    
    args = parser.parse_args()
    
    # Convert to Path objects
    schema_path = Path(args.schema).resolve()
    operations_file = Path(args.operations).resolve()
    
    # Check schema exists
    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}")
        return 1
    
    # Generate operations if needed
    if not operations_file.exists() or args.generate_ops:
        print("Generating operations file...")
        list_script = Path(__file__).parent / "list_operation_ids.py"
        try:
            subprocess.run([sys.executable, str(list_script), '--out', str(operations_file)], 
                          check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to generate operations file: {e}")
            return 2
    
    # Load operations
    entries = load_operations(operations_file)
    if not entries:
        print("No operations found in operations file")
        return 3
    
    print(f"Found {len(entries)} operations to test")
    
    # Run in batches
    total = len(entries)
    max_per_run = args.max_ops_per_run
    batches = (total + max_per_run - 1) // max_per_run
    
    success_count = 0
    fail_count = 0
    
    for i in range(batches):
        start = i * max_per_run
        end = min(start + max_per_run, total)
        batch_entries = entries[start:end]
        
        print(f"Batch {i+1}/{batches}: testing {len(batch_entries)} operations...")
        
        exit_code = run_schemathesis_batch(
            schema_path, args.base_url, batch_entries,
            args.max_examples, args.workers, args.auth_token
        )
        
        if exit_code == 0:
            success_count += 1
            print(f"Batch {i+1} completed successfully")
        else:
            fail_count += 1
            print(f"Batch {i+1} failed with exit code {exit_code}")
    
    print(f"Schemathesis run completed: {success_count} successful batches, {fail_count} failed batches")
    
    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
