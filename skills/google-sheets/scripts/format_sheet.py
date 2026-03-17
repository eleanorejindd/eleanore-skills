#!/usr/bin/env python3
"""Format a Google Sheet: bold headers, column widths, text wrapping, freeze header row."""

import argparse
import json

from auth import extract_sheet_id, get_credentials
from googleapiclient.discovery import build


def _get_sheet_id_by_title(service, spreadsheet_id: str, tab_name: str) -> int | None:
    metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sheet in metadata.get("sheets", []):
        if sheet["properties"]["title"] == tab_name:
            return sheet["properties"]["sheetId"]
    return None


def format_tab(
    sheet_id_or_url: str,
    tab_name: str,
    bold_header: bool = True,
    freeze_rows: int = 1,
    wrap_text: bool = True,
    clip_columns: list[int] | None = None,
    wrap_strategy_all: str | None = None,
    column_widths: dict[int, int] | None = None,
    auto_resize: bool = False,
) -> dict:
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    spreadsheet_id = extract_sheet_id(sheet_id_or_url)

    internal_id = _get_sheet_id_by_title(service, spreadsheet_id, tab_name)
    if internal_id is None:
        return {"error": f"Tab '{tab_name}' not found"}

    requests = []

    if bold_header:
        requests.append(
            {
                "repeatCell": {
                    "range": {"sheetId": internal_id, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {
                        "userEnteredFormat": {
                            "textFormat": {"bold": True},
                            "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
                        }
                    },
                    "fields": "userEnteredFormat(textFormat,backgroundColor)",
                }
            }
        )

    if freeze_rows > 0:
        requests.append(
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": internal_id,
                        "gridProperties": {"frozenRowCount": freeze_rows},
                    },
                    "fields": "gridProperties.frozenRowCount",
                }
            }
        )

    if wrap_strategy_all:
        requests.append(
            {
                "repeatCell": {
                    "range": {"sheetId": internal_id},
                    "cell": {"userEnteredFormat": {"wrapStrategy": wrap_strategy_all.upper()}},
                    "fields": "userEnteredFormat.wrapStrategy",
                }
            }
        )
    elif wrap_text:
        requests.append(
            {
                "repeatCell": {
                    "range": {"sheetId": internal_id},
                    "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP"}},
                    "fields": "userEnteredFormat.wrapStrategy",
                }
            }
        )

    if clip_columns:
        for col_idx in clip_columns:
            requests.append(
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": internal_id,
                            "startColumnIndex": col_idx,
                            "endColumnIndex": col_idx + 1,
                            "startRowIndex": 1,
                        },
                        "cell": {"userEnteredFormat": {"wrapStrategy": "CLIP"}},
                        "fields": "userEnteredFormat.wrapStrategy",
                    }
                }
            )

    if column_widths:
        for col_idx, width in column_widths.items():
            requests.append(
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": internal_id,
                            "dimension": "COLUMNS",
                            "startIndex": col_idx,
                            "endIndex": col_idx + 1,
                        },
                        "properties": {"pixelSize": width},
                        "fields": "pixelSize",
                    }
                }
            )

    if auto_resize:
        requests.append(
            {
                "autoResizeDimensions": {
                    "dimensions": {
                        "sheetId": internal_id,
                        "dimension": "COLUMNS",
                        "startIndex": 0,
                        "endIndex": 26,
                    }
                }
            }
        )

    if requests:
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests}).execute()

    return {"spreadsheet_id": spreadsheet_id, "tab": tab_name, "formats_applied": len(requests)}


def main():
    parser = argparse.ArgumentParser(description="Format a Google Sheet tab")
    parser.add_argument("sheet_id", help="Spreadsheet ID or URL")
    parser.add_argument("--tab", required=True, help="Tab name to format")
    parser.add_argument("--no-bold-header", action="store_true")
    parser.add_argument("--no-wrap", action="store_true")
    parser.add_argument("--wrap-strategy-all", help="Set wrap strategy for entire sheet: WRAP, CLIP, OVERFLOW_CELL")
    parser.add_argument("--clip-columns", help="JSON array of column indices to set CLIP on, e.g. [3,5,16]")
    parser.add_argument("--freeze-rows", type=int, default=1)
    parser.add_argument("--auto-resize", action="store_true")
    parser.add_argument("--column-widths", help='JSON object of col_index:width, e.g. \'{"0":100,"1":80}\'')
    args = parser.parse_args()

    col_widths = json.loads(args.column_widths) if args.column_widths else None
    if col_widths:
        col_widths = {int(k): v for k, v in col_widths.items()}

    clip_cols = json.loads(args.clip_columns) if args.clip_columns else None

    result = format_tab(
        args.sheet_id,
        args.tab,
        bold_header=not args.no_bold_header,
        freeze_rows=args.freeze_rows,
        wrap_text=not args.no_wrap,
        wrap_strategy_all=args.wrap_strategy_all,
        clip_columns=clip_cols,
        column_widths=col_widths,
        auto_resize=args.auto_resize,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
