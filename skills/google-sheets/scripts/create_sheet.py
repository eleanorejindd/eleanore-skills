#!/usr/bin/env python3
"""Create a new Google Sheet with optional column headers and tabs."""

import argparse
import json

from auth import get_credentials
from googleapiclient.discovery import build


def create_sheet(title: str, columns: list[str] | None = None, tabs: list[str] | None = None) -> dict:
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)

    sheets = []
    if tabs:
        sheets = [{"properties": {"title": tab}} for tab in tabs]
    else:
        sheets = [{"properties": {"title": "Sheet1"}}]

    body = {"properties": {"title": title}, "sheets": sheets}
    spreadsheet = service.spreadsheets().create(body=body).execute()
    sheet_id = spreadsheet["spreadsheetId"]
    sheet_url = spreadsheet["spreadsheetUrl"]

    if columns:
        tab_name = tabs[0] if tabs else "Sheet1"
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"{tab_name}!A1",
            valueInputOption="RAW",
            body={"values": [columns]},
        ).execute()

    return {"id": sheet_id, "url": sheet_url, "title": title}


def main():
    parser = argparse.ArgumentParser(description="Create a Google Sheet")
    parser.add_argument("title", help="Title for the new spreadsheet")
    parser.add_argument("--columns", help="Comma-separated column headers for the first row")
    parser.add_argument("--tabs", help="Comma-separated tab/sheet names (default: Sheet1)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    columns = [c.strip() for c in args.columns.split(",")] if args.columns else None
    tabs = [t.strip() for t in args.tabs.split(",")] if args.tabs else None

    result = create_sheet(args.title, columns=columns, tabs=tabs)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Created: {result['title']}")
        print(f"ID: {result['id']}")
        print(f"URL: {result['url']}")


if __name__ == "__main__":
    main()
