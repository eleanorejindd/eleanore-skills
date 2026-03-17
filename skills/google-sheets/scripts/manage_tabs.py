#!/usr/bin/env python3
"""Manage tabs (sheets) within a Google Spreadsheet: add, delete, rename."""

import argparse
import json
import sys

from auth import extract_sheet_id, get_credentials
from googleapiclient.discovery import build


def _get_sheet_id_by_title(service, spreadsheet_id: str, tab_name: str) -> int | None:
    """Get the internal sheetId for a tab by its title."""
    metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sheet in metadata.get("sheets", []):
        if sheet["properties"]["title"] == tab_name:
            return sheet["properties"]["sheetId"]
    return None


def add_tab(sheet_id_or_url: str, tab_name: str, headers: list[str] | None = None, index: int | None = None) -> dict:
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    spreadsheet_id = extract_sheet_id(sheet_id_or_url)

    properties: dict = {"title": tab_name}
    if index is not None:
        properties["index"] = index

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": [{"addSheet": {"properties": properties}}]},
    ).execute()

    if headers:
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{tab_name}!A1",
            valueInputOption="RAW",
            body={"values": [headers]},
        ).execute()

    return {"action": "add_tab", "spreadsheet_id": spreadsheet_id, "tab": tab_name, "index": index}


def delete_tab(sheet_id_or_url: str, tab_name: str) -> dict:
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    spreadsheet_id = extract_sheet_id(sheet_id_or_url)

    internal_id = _get_sheet_id_by_title(service, spreadsheet_id, tab_name)
    if internal_id is None:
        return {"error": f"Tab '{tab_name}' not found"}

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": [{"deleteSheet": {"sheetId": internal_id}}]},
    ).execute()

    return {"action": "delete_tab", "spreadsheet_id": spreadsheet_id, "tab": tab_name}


def move_tab(sheet_id_or_url: str, tab_name: str, index: int) -> dict:
    """Move a tab to a specific position (0-indexed)."""
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    spreadsheet_id = extract_sheet_id(sheet_id_or_url)

    internal_id = _get_sheet_id_by_title(service, spreadsheet_id, tab_name)
    if internal_id is None:
        return {"error": f"Tab '{tab_name}' not found"}

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {"sheetId": internal_id, "index": index},
                        "fields": "index",
                    }
                }
            ]
        },
    ).execute()

    return {"action": "move_tab", "spreadsheet_id": spreadsheet_id, "tab": tab_name, "index": index}


def main():
    parser = argparse.ArgumentParser(description="Manage Google Sheet tabs")
    parser.add_argument("sheet_id", help="Spreadsheet ID or URL")

    sub = parser.add_subparsers(dest="action", required=True)

    add_p = sub.add_parser("add", help="Add a new tab")
    add_p.add_argument("tab_name", help="Name for the new tab")
    add_p.add_argument("--headers", help="Comma-separated column headers")
    add_p.add_argument("--index", type=int, help="Tab position (0-indexed, 0=first)")

    del_p = sub.add_parser("delete", help="Delete a tab")
    del_p.add_argument("tab_name", help="Name of the tab to delete")

    move_p = sub.add_parser("move", help="Move a tab to a position")
    move_p.add_argument("tab_name", help="Name of the tab to move")
    move_p.add_argument("index", type=int, help="Target position (0-indexed, 0=first)")

    args = parser.parse_args()

    if args.action == "add":
        headers = [h.strip() for h in args.headers.split(",")] if args.headers else None
        result = add_tab(args.sheet_id, args.tab_name, headers=headers, index=args.index)
    elif args.action == "delete":
        result = delete_tab(args.sheet_id, args.tab_name)
    elif args.action == "move":
        result = move_tab(args.sheet_id, args.tab_name, args.index)
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
