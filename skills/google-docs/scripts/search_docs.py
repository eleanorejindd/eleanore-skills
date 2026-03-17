#!/usr/bin/env python3
"""
Search for Google Docs by name.

Usage:
    python3 search_docs.py "<query>" [--limit N] [--json]

Examples:
    python3 search_docs.py "self eval"
    python3 search_docs.py "self eval" --limit 5
    python3 search_docs.py "self eval" --json
"""

# Suppress warnings before any Google imports
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

import importlib.metadata  # noqa: E402

if not hasattr(importlib.metadata, "packages_distributions"):
    importlib.metadata.packages_distributions = lambda: {}

import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
from typing import Any  # noqa: E402

from auth import get_credentials  # noqa: E402
from googleapiclient.discovery import build  # noqa: E402


def search_docs(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """
    Search for Google Docs by name.

    Args:
        query: Search query (name contains)
        limit: Maximum number of results

    Returns:
        List of document metadata dicts
    """
    creds = get_credentials()
    drive_service = build("drive", "v3", credentials=creds)

    # Escape single quotes in query
    escaped_query = query.replace("'", "\\'")

    # Search for Google Docs containing the query in name
    response = (
        drive_service.files()
        .list(
            q=f"name contains '{escaped_query}' and mimeType='application/vnd.google-apps.document' and trashed=false",
            pageSize=limit,
            fields="files(id, name, createdTime, modifiedTime, webViewLink)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
    )

    files = response.get("files", [])

    results = []
    for f in files:
        results.append(
            {
                "id": f["id"],
                "name": f["name"],
                "createdTime": f.get("createdTime"),
                "modifiedTime": f.get("modifiedTime"),
                "webViewLink": f.get("webViewLink"),
            }
        )

    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Search for Google Docs by name")
    parser.add_argument("query", help="Search query (name contains)")
    parser.add_argument("--limit", type=int, default=10, help="Maximum results (default: 10)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    try:
        results = search_docs(args.query, args.limit)

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            if not results:
                print(f"No Google Docs found matching '{args.query}'")
            else:
                print(f"Found {len(results)} Google Doc(s) matching '{args.query}':\n")
                for doc in results:
                    print(f"  Name: {doc['name']}")
                    print(f"  ID: {doc['id']}")
                    print(f"  Modified: {doc['modifiedTime']}")
                    print(f"  Link: {doc['webViewLink']}")
                    print()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
