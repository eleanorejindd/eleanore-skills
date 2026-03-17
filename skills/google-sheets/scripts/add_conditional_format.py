#!/usr/bin/env python3
"""Add conditional formatting rules to a Google Sheet column."""

import argparse
import json

from auth import extract_sheet_id, get_credentials
from googleapiclient.discovery import build


def add_text_color_rules(
    sheet_id_or_url: str,
    tab_name: str,
    col_index: int,
    rules: list[dict],
    start_row: int = 1,
) -> dict:
    """
    Add conditional formatting rules that color cells based on text content.

    rules: list of {"text": "value", "bg": {"red": R, "green": G, "blue": B}, "fg": {...}}
    """
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    spreadsheet_id = extract_sheet_id(sheet_id_or_url)

    metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    internal_id = None
    for sheet in metadata.get("sheets", []):
        if sheet["properties"]["title"] == tab_name:
            internal_id = sheet["properties"]["sheetId"]
            break
    if internal_id is None:
        return {"error": f"Tab '{tab_name}' not found"}

    requests = []
    for rule in rules:
        fmt = {}
        if "bg" in rule:
            fmt["backgroundColor"] = rule["bg"]
        if "fg" in rule:
            fmt["textFormat"] = {"foregroundColor": rule["fg"]}

        requests.append(
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [
                            {
                                "sheetId": internal_id,
                                "startRowIndex": start_row,
                                "startColumnIndex": col_index,
                                "endColumnIndex": col_index + 1,
                            }
                        ],
                        "booleanRule": {
                            "condition": {
                                "type": "TEXT_EQ",
                                "values": [{"userEnteredValue": rule["text"]}],
                            },
                            "format": fmt,
                        },
                    },
                    "index": 0,
                }
            }
        )

    if requests:
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests}).execute()

    return {"spreadsheet_id": spreadsheet_id, "tab": tab_name, "column": col_index, "rules_added": len(requests)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add conditional formatting")
    parser.add_argument("sheet_id")
    parser.add_argument("--tab", required=True)
    parser.add_argument("--column", type=int, required=True)
    parser.add_argument("--rules", required=True, help="JSON array of rules")
    args = parser.parse_args()

    result = add_text_color_rules(args.sheet_id, args.tab, args.column, json.loads(args.rules))
    print(json.dumps(result, indent=2))
