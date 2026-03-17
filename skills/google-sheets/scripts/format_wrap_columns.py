#!/usr/bin/env python3
"""Set specific columns to WRAP strategy (data rows only, not header)."""

import argparse
import json

from auth import extract_sheet_id, get_credentials
from googleapiclient.discovery import build


def set_wrap_columns(sheet_id_or_url: str, tab_name: str, columns: list[int]) -> dict:
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
    for col_idx in columns:
        requests.append(
            {
                "repeatCell": {
                    "range": {
                        "sheetId": internal_id,
                        "startColumnIndex": col_idx,
                        "endColumnIndex": col_idx + 1,
                        "startRowIndex": 1,
                    },
                    "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP"}},
                    "fields": "userEnteredFormat.wrapStrategy",
                }
            }
        )

    if requests:
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests}).execute()

    return {"spreadsheet_id": spreadsheet_id, "tab": tab_name, "wrap_columns": columns}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("sheet_id")
    parser.add_argument("--tab", required=True)
    parser.add_argument("--columns", required=True, help="JSON array of column indices")
    args = parser.parse_args()
    result = set_wrap_columns(args.sheet_id, args.tab, json.loads(args.columns))
    print(json.dumps(result, indent=2))
