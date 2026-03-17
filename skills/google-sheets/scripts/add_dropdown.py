#!/usr/bin/env python3
"""Add dropdown data validation to a column in a Google Sheet."""

import argparse
import json

from auth import extract_sheet_id, get_credentials
from googleapiclient.discovery import build


def add_dropdown(sheet_id_or_url: str, tab_name: str, col_index: int, values: list[str], start_row: int = 1) -> dict:
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

    condition_values = [{"userEnteredValue": v} for v in values]

    requests = [
        {
            "setDataValidation": {
                "range": {
                    "sheetId": internal_id,
                    "startRowIndex": start_row,
                    "startColumnIndex": col_index,
                    "endColumnIndex": col_index + 1,
                },
                "rule": {
                    "condition": {
                        "type": "ONE_OF_LIST",
                        "values": condition_values,
                    },
                    "showCustomUi": True,
                    "strict": False,
                },
            }
        }
    ]

    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests}).execute()

    return {"spreadsheet_id": spreadsheet_id, "tab": tab_name, "column": col_index, "values": values}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add dropdown validation to a column")
    parser.add_argument("sheet_id", help="Spreadsheet ID or URL")
    parser.add_argument("--tab", required=True, help="Tab name")
    parser.add_argument("--column", type=int, required=True, help="Column index (0-based)")
    parser.add_argument("--values", required=True, help="JSON array of dropdown values")
    args = parser.parse_args()

    result = add_dropdown(args.sheet_id, args.tab, args.column, json.loads(args.values))
    print(json.dumps(result, indent=2))
