#!/usr/bin/env python3
"""Write data to a Google Sheet (append rows, update cells, or clear)."""

import argparse
import json
import sys

from auth import extract_sheet_id, get_credentials
from googleapiclient.discovery import build


def append_rows(sheet_id_or_url: str, tab: str, rows: list[list[str]]) -> dict:
    """Append rows to the end of a sheet tab."""
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    sheet_id = extract_sheet_id(sheet_id_or_url)

    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=sheet_id,
            range=f"{tab}!A1",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": rows},
        )
        .execute()
    )

    updates = result.get("updates", {})
    return {
        "sheet_id": sheet_id,
        "updated_range": updates.get("updatedRange", ""),
        "updated_rows": updates.get("updatedRows", 0),
    }


def update_cells(sheet_id_or_url: str, tab: str, range_str: str, values: list[list[str]]) -> dict:
    """Update specific cells in a sheet."""
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    sheet_id = extract_sheet_id(sheet_id_or_url)

    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=sheet_id,
            range=f"{tab}!{range_str}",
            valueInputOption="USER_ENTERED",
            body={"values": values},
        )
        .execute()
    )

    return {
        "sheet_id": sheet_id,
        "updated_range": result.get("updatedRange", ""),
        "updated_cells": result.get("updatedCells", 0),
    }


def clear_range(sheet_id_or_url: str, tab: str, range_str: str | None = None) -> dict:
    """Clear cells in a range (or entire tab)."""
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    sheet_id = extract_sheet_id(sheet_id_or_url)

    full_range = f"{tab}!{range_str}" if range_str else tab

    service.spreadsheets().values().clear(spreadsheetId=sheet_id, range=full_range, body={}).execute()

    return {"sheet_id": sheet_id, "cleared_range": full_range}


def main():
    parser = argparse.ArgumentParser(description="Write to a Google Sheet")
    parser.add_argument("sheet_id", help="Spreadsheet ID or URL")
    parser.add_argument("--tab", default="Sheet1", help="Tab/sheet name (default: Sheet1)")

    sub = parser.add_subparsers(dest="action", required=True)

    append_p = sub.add_parser("append", help="Append rows")
    append_p.add_argument("data", help='JSON array of rows, e.g. \'[["a","b"],["c","d"]]\'')

    update_p = sub.add_parser("update", help="Update specific cells")
    update_p.add_argument("range", help="Cell range (e.g., A1:B2)")
    update_p.add_argument("data", help="JSON array of rows")

    clear_p = sub.add_parser("clear", help="Clear a range")
    clear_p.add_argument("--range", dest="range_str", help="Cell range to clear (omit for entire tab)")

    args = parser.parse_args()

    if args.action == "append":
        rows = json.loads(args.data)
        result = append_rows(args.sheet_id, args.tab, rows)
    elif args.action == "update":
        values = json.loads(args.data)
        result = update_cells(args.sheet_id, args.tab, args.range, values)
    elif args.action == "clear":
        result = clear_range(args.sheet_id, args.tab, args.range_str)
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
