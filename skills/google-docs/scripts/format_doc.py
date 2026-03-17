#!/usr/bin/env python3
"""
Insert formatted content into a Google Doc: headings, tables, code blocks, lists.

Works by building Google Docs API batchUpdate requests. Inserts at end of doc
by default, or after a specific heading.

Usage:
    python3 format_doc.py <doc_id> heading <level> <text>
    python3 format_doc.py <doc_id> table <json_rows>
    python3 format_doc.py <doc_id> code <text> [--lang python]
    python3 format_doc.py <doc_id> bullets <json_items>
    python3 format_doc.py <doc_id> numbered <json_items>
    python3 format_doc.py <doc_id> markdown --file <path>    # parse markdown file
    python3 format_doc.py <doc_id> markdown <text>           # parse markdown string

    Add --after "Heading text" to insert after a specific heading instead of at end.
"""

import argparse
import json
import re
import sys
from typing import Any

from auth import extract_doc_id, get_credentials
from googleapiclient.discovery import build

HEADING_STYLES = {
    1: "HEADING_1",
    2: "HEADING_2",
    3: "HEADING_3",
    4: "HEADING_4",
    5: "HEADING_5",
    6: "HEADING_6",
}


def _get_doc_end_index(service, doc_id: str) -> int:
    doc = service.documents().get(documentId=doc_id).execute()
    content = doc.get("body", {}).get("content", [])
    return content[-1]["endIndex"] - 1 if content else 1


def _find_heading_end(service, doc_id: str, heading_text: str) -> int | None:
    doc = service.documents().get(documentId=doc_id).execute()
    body_content = doc.get("body", {}).get("content", [])

    for i, element in enumerate(body_content):
        if "paragraph" not in element:
            continue
        para_text = ""
        for pe in element["paragraph"].get("elements", []):
            if "textRun" in pe:
                para_text += pe["textRun"].get("content", "")

        if heading_text.strip().lower() in para_text.strip().lower():
            if i + 1 < len(body_content):
                return body_content[i + 1]["startIndex"]
            return element["endIndex"] - 1

    return None


def insert_heading(service, doc_id: str, level: int, text: str, index: int) -> int:
    """Insert a heading. Returns the index after insertion."""
    style_name = HEADING_STYLES.get(level, "HEADING_1")
    insert_text = f"\n{text}\n"

    requests = [
        {"insertText": {"location": {"index": index}, "text": insert_text}},
        {
            "updateParagraphStyle": {
                "range": {
                    "startIndex": index + 1,
                    "endIndex": index + 1 + len(text),
                },
                "paragraphStyle": {"namedStyleType": style_name},
                "fields": "namedStyleType",
            }
        },
    ]

    service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

    return index + len(insert_text)


def insert_table(service, doc_id: str, rows: list[list[str]], index: int) -> int:
    """Insert a table with data. First row treated as header."""
    if not rows:
        return index

    n_rows = len(rows)
    n_cols = max(len(row) for row in rows)

    requests = [
        {
            "insertTable": {
                "rows": n_rows,
                "columns": n_cols,
                "location": {"index": index},
            }
        }
    ]

    service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

    doc = service.documents().get(documentId=doc_id).execute()
    body_content = doc.get("body", {}).get("content", [])

    table_element = None
    for element in body_content:
        if "table" in element and element["startIndex"] >= index:
            table_element = element["table"]
            break

    if not table_element:
        print("Warning: could not find inserted table", file=sys.stderr)
        return index

    cell_inserts: list[tuple[int, str, bool]] = []

    table_rows = table_element.get("tableRows", [])
    for row_idx, table_row in enumerate(table_rows):
        cells = table_row.get("tableCells", [])
        for col_idx, cell in enumerate(cells):
            if row_idx < len(rows) and col_idx < len(rows[row_idx]):
                cell_text = rows[row_idx][col_idx]
                cell_content = cell.get("content", [])
                if cell_content and cell_text:
                    cell_start = cell_content[0].get("startIndex", 0)
                    is_header = row_idx == 0
                    cell_inserts.append((cell_start, cell_text, is_header))

    # Insert in reverse index order so earlier inserts don't shift later indices
    cell_inserts.sort(key=lambda x: x[0], reverse=True)

    for cell_start, cell_text, is_header in cell_inserts:
        reqs: list[dict[str, Any]] = [{"insertText": {"location": {"index": cell_start}, "text": cell_text}}]
        if is_header:
            reqs.append(
                {
                    "updateTextStyle": {
                        "range": {"startIndex": cell_start, "endIndex": cell_start + len(cell_text)},
                        "textStyle": {"bold": True},
                        "fields": "bold",
                    }
                }
            )
        service.documents().batchUpdate(documentId=doc_id, body={"requests": reqs}).execute()

    doc = service.documents().get(documentId=doc_id).execute()
    body_content = doc.get("body", {}).get("content", [])
    for element in body_content:
        if "table" in element and element["startIndex"] >= index:
            return element["endIndex"]

    return index


def insert_code_block(service, doc_id: str, code: str, index: int, lang: str = "") -> int:
    """Insert a code block with monospace font and light gray background."""
    insert_text = f"\n{code}\n"

    requests = [
        {"insertText": {"location": {"index": index}, "text": insert_text}},
        {
            "updateTextStyle": {
                "range": {
                    "startIndex": index + 1,
                    "endIndex": index + 1 + len(code),
                },
                "textStyle": {
                    "weightedFontFamily": {
                        "fontFamily": "Courier New",
                        "weight": 400,
                    },
                    "fontSize": {"magnitude": 10, "unit": "PT"},
                },
                "fields": "weightedFontFamily,fontSize",
            }
        },
        {
            "updateParagraphStyle": {
                "range": {
                    "startIndex": index + 1,
                    "endIndex": index + 1 + len(code),
                },
                "paragraphStyle": {
                    "shading": {
                        "backgroundColor": {
                            "color": {
                                "rgbColor": {
                                    "red": 0.95,
                                    "green": 0.95,
                                    "blue": 0.95,
                                }
                            }
                        }
                    },
                    "indentStart": {"magnitude": 18, "unit": "PT"},
                    "indentEnd": {"magnitude": 18, "unit": "PT"},
                    "spaceAbove": {"magnitude": 6, "unit": "PT"},
                    "spaceBelow": {"magnitude": 6, "unit": "PT"},
                },
                "fields": "shading,indentStart,indentEnd,spaceAbove,spaceBelow",
            }
        },
    ]

    service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

    return index + len(insert_text)


def insert_list(service, doc_id: str, items: list[str], ordered: bool, index: int) -> int:
    """Insert a bullet or numbered list."""
    text_block = "\n".join(items) + "\n"
    insert_text = f"\n{text_block}"

    requests = [
        {"insertText": {"location": {"index": index}, "text": insert_text}},
        {
            "createParagraphBullets": {
                "range": {
                    "startIndex": index + 1,
                    "endIndex": index + len(insert_text),
                },
                "bulletPreset": "NUMBERED_DECIMAL_ALPHA_ROMAN" if ordered else "BULLET_DISC_CIRCLE_SQUARE",
            }
        },
    ]

    service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

    return index + len(insert_text)


def insert_markdown(service, doc_id: str, markdown_text: str, start_index: int) -> int:
    """
    Parse a markdown string and insert formatted content into the doc.

    Supported markdown:
    - # H1 through ###### H6
    - **bold**, *italic*, `inline code`, ~~strikethrough~~
    - - bullet items
    - 1. numbered items
    - ```code blocks```
    - | table | rows |
    """
    lines = markdown_text.split("\n")
    idx = start_index
    i = 0

    while i < len(lines):
        line = lines[i]

        if line.startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1
            if code_lines:
                idx = insert_code_block(service, doc_id, "\n".join(code_lines), idx)
            continue

        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s\-:|]+\|", lines[i + 1]):
            table_lines = [line]
            i += 1
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|[\s\-:|]+\|$", lines[i]):
                    table_lines.append(lines[i])
                i += 1
            rows = []
            for tl in table_lines:
                cells = [c.strip() for c in tl.strip("|").split("|")]
                rows.append(cells)
            if rows:
                idx = insert_table(service, doc_id, rows, idx)
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            idx = insert_heading(service, doc_id, level, text, idx)
            i += 1
            continue

        bullet_items = []
        if re.match(r"^\s*[-*]\s+", line):
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                bullet_items.append(re.sub(r"^\s*[-*]\s+", "", lines[i]))
                i += 1
            idx = insert_list(service, doc_id, bullet_items, ordered=False, index=idx)
            continue

        numbered_items = []
        if re.match(r"^\s*\d+\.\s+", line):
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                numbered_items.append(re.sub(r"^\s*\d+\.\s+", "", lines[i]))
                i += 1
            idx = insert_list(service, doc_id, numbered_items, ordered=True, index=idx)
            continue

        if line.strip():
            insert_text = f"\n{line}"
            reqs: list[dict[str, Any]] = [{"insertText": {"location": {"index": idx}, "text": insert_text}}]

            style_ranges: list[tuple[str, int, int]] = []
            offset = idx + 1

            for pattern, style in [
                (r"\*\*\*(.+?)\*\*\*", "bolditalic"),
                (r"\*\*(.+?)\*\*", "bold"),
                (r"\*(.+?)\*", "italic"),
                (r"`(.+?)`", "code"),
                (r"~~(.+?)~~", "strikethrough"),
            ]:
                for m in re.finditer(pattern, line):
                    start_in_line = m.start()
                    actual_start = offset + start_in_line
                    style_ranges.append((style, actual_start, actual_start + len(m.group(0))))

            service.documents().batchUpdate(documentId=doc_id, body={"requests": reqs}).execute()

            if style_ranges:
                style_reqs = []
                for style, s, e in style_ranges:
                    if style == "bold":
                        style_reqs.append(
                            {
                                "updateTextStyle": {
                                    "range": {"startIndex": s, "endIndex": e},
                                    "textStyle": {"bold": True},
                                    "fields": "bold",
                                }
                            }
                        )
                    elif style == "italic":
                        style_reqs.append(
                            {
                                "updateTextStyle": {
                                    "range": {"startIndex": s, "endIndex": e},
                                    "textStyle": {"italic": True},
                                    "fields": "italic",
                                }
                            }
                        )
                    elif style == "bolditalic":
                        style_reqs.append(
                            {
                                "updateTextStyle": {
                                    "range": {"startIndex": s, "endIndex": e},
                                    "textStyle": {"bold": True, "italic": True},
                                    "fields": "bold,italic",
                                }
                            }
                        )
                    elif style == "code":
                        style_reqs.append(
                            {
                                "updateTextStyle": {
                                    "range": {"startIndex": s, "endIndex": e},
                                    "textStyle": {
                                        "weightedFontFamily": {
                                            "fontFamily": "Courier New",
                                            "weight": 400,
                                        }
                                    },
                                    "fields": "weightedFontFamily",
                                }
                            }
                        )
                    elif style == "strikethrough":
                        style_reqs.append(
                            {
                                "updateTextStyle": {
                                    "range": {"startIndex": s, "endIndex": e},
                                    "textStyle": {"strikethrough": True},
                                    "fields": "strikethrough",
                                }
                            }
                        )

                if style_reqs:
                    service.documents().batchUpdate(documentId=doc_id, body={"requests": style_reqs}).execute()

            idx += len(insert_text)

        i += 1

    return idx


def main():
    parser = argparse.ArgumentParser(description="Insert formatted content into a Google Doc")
    parser.add_argument("doc_id", help="Document ID or URL")
    parser.add_argument("--after", help="Insert after this heading (default: end of doc)")

    sub = parser.add_subparsers(dest="action", required=True)

    h = sub.add_parser("heading", help="Insert a heading")
    h.add_argument("level", type=int, choices=[1, 2, 3, 4, 5, 6])
    h.add_argument("text", help="Heading text")

    t = sub.add_parser("table", help="Insert a table")
    t.add_argument("rows_json", help='JSON array of rows: [["H1","H2"],["a","b"]]')

    c = sub.add_parser("code", help="Insert a code block")
    c.add_argument("text", help="Code text")
    c.add_argument("--lang", default="", help="Language hint (for display only)")

    b = sub.add_parser("bullets", help="Insert a bullet list")
    b.add_argument("items_json", help='JSON array of strings: ["item1","item2"]')

    n = sub.add_parser("numbered", help="Insert a numbered list")
    n.add_argument("items_json", help='JSON array of strings: ["item1","item2"]')

    m = sub.add_parser("markdown", help="Parse and insert markdown content")
    m.add_argument("text", nargs="?", help="Markdown text")
    m.add_argument("--file", dest="file_path", help="Read markdown from file")

    args = parser.parse_args()

    creds = get_credentials()
    service = build("docs", "v1", credentials=creds)
    doc_id = extract_doc_id(args.doc_id)

    if args.after:
        idx = _find_heading_end(service, doc_id, args.after)
        if idx is None:
            print(f"Error: heading '{args.after}' not found", file=sys.stderr)
            sys.exit(1)
    else:
        idx = _get_doc_end_index(service, doc_id)

    result = {"doc_id": doc_id, "action": args.action, "insert_index": idx}

    if args.action == "heading":
        end = insert_heading(service, doc_id, args.level, args.text, idx)
        result["end_index"] = end

    elif args.action == "table":
        rows = json.loads(args.rows_json)
        end = insert_table(service, doc_id, rows, idx)
        result["end_index"] = end
        result["rows"] = len(rows)

    elif args.action == "code":
        end = insert_code_block(service, doc_id, args.text, idx, args.lang)
        result["end_index"] = end

    elif args.action == "bullets":
        items = json.loads(args.items_json)
        end = insert_list(service, doc_id, items, ordered=False, index=idx)
        result["end_index"] = end
        result["items"] = len(items)

    elif args.action == "numbered":
        items = json.loads(args.items_json)
        end = insert_list(service, doc_id, items, ordered=True, index=idx)
        result["end_index"] = end
        result["items"] = len(items)

    elif args.action == "markdown":
        if args.file_path:
            with open(args.file_path) as f:
                md_text = f.read()
        elif args.text:
            md_text = args.text
        else:
            print("Error: provide markdown text or --file", file=sys.stderr)
            sys.exit(1)
        end = insert_markdown(service, doc_id, md_text, idx)
        result["end_index"] = end

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
