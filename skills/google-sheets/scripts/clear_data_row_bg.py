#!/usr/bin/env python3
"""Clear background color from data rows (row 2 onward), keeping header background intact."""

import argparse
import json

from auth import extract_sheet_id, get_credentials
from googleapiclient.discovery import build


def clear_data_bg(sheet_id_or_url: str, tab_name: str) -> dict:
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

    requests = [
        {
            "repeatCell": {
                "range": {"sheetId": internal_id, "startRowIndex": 1},
                "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}},
                "fields": "userEnteredFormat.backgroundColor",
            }
        }
    ]

    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests}).execute()

    return {"spreadsheet_id": spreadsheet_id, "tab": tab_name, "status": "cleared"}


def main():
    parser = argparse.ArgumentParser(description="Clear background color from data rows")
    parser.add_argument("sheet_id", help="Spreadsheet ID or URL")
    parser.add_argument("--tab", required=True, help="Tab name")
    args = parser.parse_args()
    result = clear_data_bg(args.sheet_id, args.tab)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
