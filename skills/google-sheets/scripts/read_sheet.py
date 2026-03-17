#!/usr/bin/env python3
"""Read data from a Google Sheet."""

import argparse
import json

from auth import extract_sheet_id, get_credentials
from googleapiclient.discovery import build


def read_sheet(sheet_id_or_url: str, tab: str = "Sheet1", range_str: str | None = None) -> dict:
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    sheet_id = extract_sheet_id(sheet_id_or_url)

    if range_str:
        full_range = f"{tab}!{range_str}"
    else:
        full_range = tab

    result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=full_range).execute()

    values = result.get("values", [])
    return {"sheet_id": sheet_id, "range": full_range, "rows": values}


def list_tabs(sheet_id_or_url: str) -> list[str]:
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    sheet_id = extract_sheet_id(sheet_id_or_url)

    metadata = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    return [s["properties"]["title"] for s in metadata.get("sheets", [])]


def format_as_markdown(rows: list[list[str]]) -> str:
    if not rows:
        return "(empty)"
    headers = rows[0]
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows[1:]:
        padded = row + [""] * (len(headers) - len(row))
        lines.append("| " + " | ".join(padded) + " |")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Read a Google Sheet")
    parser.add_argument("sheet_id", help="Spreadsheet ID or URL")
    parser.add_argument("--tab", default="Sheet1", help="Tab/sheet name (default: Sheet1)")
    parser.add_argument("--range", dest="range_str", help="Cell range (e.g., A1:D10)")
    parser.add_argument("--list-tabs", action="store_true", help="List all tab names")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.list_tabs:
        tabs = list_tabs(args.sheet_id)
        if args.json:
            print(json.dumps(tabs))
        else:
            for t in tabs:
                print(f"  - {t}")
        return

    result = read_sheet(args.sheet_id, tab=args.tab, range_str=args.range_str)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_as_markdown(result["rows"]))


if __name__ == "__main__":
    main()
