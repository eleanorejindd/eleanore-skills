#!/usr/bin/env python3
"""
Fetch content from a Google Doc with formatting preserved as markdown.

Supports: headings, bold, italic, code, strikethrough, links, images,
tables, bullet/numbered lists, and multi-tab documents.

Usage:
    python3 fetch_doc.py <doc_id_or_url> [output_file]
"""

import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

import importlib.metadata  # noqa: E402

if not hasattr(importlib.metadata, "packages_distributions"):
    importlib.metadata.packages_distributions = lambda: {}

from pathlib import Path  # noqa: E402
import sys  # noqa: E402
from typing import Any  # noqa: E402

from auth import extract_doc_id, get_credentials  # noqa: E402
from googleapiclient.discovery import build  # noqa: E402
import requests  # noqa: E402

_inline_objects: dict[str, dict] = {}
_images_dir: Path | None = None
_image_counter: int = 0
_credentials = None
_lists: dict[str, dict] = {}

HEADING_MAP = {
    "HEADING_1": "# ",
    "HEADING_2": "## ",
    "HEADING_3": "### ",
    "HEADING_4": "#### ",
    "HEADING_5": "##### ",
    "HEADING_6": "###### ",
    "TITLE": "# ",
    "SUBTITLE": "## ",
}

CODE_BLOCK_MARKER = "\ue907"


def download_image(uri: str, description: str = "") -> str | None:
    global _image_counter, _images_dir, _credentials

    if not _images_dir:
        return None

    _image_counter += 1

    try:
        headers = {}
        if ("googleusercontent.com" in uri or "google.com" in uri) and _credentials:
            headers["Authorization"] = f"Bearer {_credentials.token}"

        response = requests.get(uri, headers=headers, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "image/png")
        ext_map = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "image/svg+xml": ".svg",
        }
        ext = ext_map.get(content_type.split(";")[0], ".png")

        filename = f"image_{_image_counter:03d}{ext}"
        filepath = _images_dir / filename

        with open(filepath, "wb") as f:
            f.write(response.content)

        print(f"  Downloaded: {filename}", file=sys.stderr)
        return f"images/{filename}"

    except Exception as e:
        print(f"  Warning: Failed to download image: {e}", file=sys.stderr)
        return None


def _format_text_run(text_run: dict, in_code_block: bool = False) -> str:
    """Apply inline formatting (bold, italic, code, strikethrough) to a text run."""
    content = text_run.get("content", "")
    text_style = text_run.get("textStyle", {})

    link_url = text_style.get("link", {}).get("url", "")

    stripped = content.rstrip("\n")
    trailing = content[len(stripped) :]

    if not stripped:
        return content

    is_bold = text_style.get("bold", False)
    is_italic = text_style.get("italic", False)
    is_strikethrough = text_style.get("strikethrough", False)

    font_family = text_style.get("weightedFontFamily", {}).get("fontFamily", "")
    is_code = font_family in MONOSPACE_FONTS

    formatted = stripped

    if in_code_block:
        return content

    if is_code:
        formatted = f"`{formatted}`"
    else:
        if is_bold and is_italic:
            formatted = f"***{formatted}***"
        elif is_bold:
            formatted = f"**{formatted}**"
        elif is_italic:
            formatted = f"*{formatted}*"

    if is_strikethrough:
        formatted = f"~~{formatted}~~"

    if link_url:
        formatted = f"[{formatted}]({link_url})"

    return formatted + trailing


MONOSPACE_FONTS = frozenset(
    {
        "Courier New",
        "Consolas",
        "Source Code Pro",
        "Roboto Mono",
        "monospace",
        "Fira Code",
        "JetBrains Mono",
        "Inconsolata",
    }
)


def _is_code_block_paragraph(paragraph: dict) -> bool:
    """Detect code block paragraphs: native (\ue907) or styled (all-monospace with shading/indent)."""
    elements = paragraph.get("elements", [])
    para_style = paragraph.get("paragraphStyle", {})

    has_marker = False
    all_monospace = True
    has_text = False

    for pe in elements:
        if "textRun" not in pe:
            continue
        tr = pe["textRun"]
        content = tr.get("content", "")

        if content.startswith(CODE_BLOCK_MARKER):
            has_marker = True

        stripped = content.strip()
        if not stripped:
            continue

        has_text = True
        font = tr.get("textStyle", {}).get("weightedFontFamily", {}).get("fontFamily", "")
        if font not in MONOSPACE_FONTS and not content.startswith(CODE_BLOCK_MARKER):
            all_monospace = False

    if has_marker:
        return True

    if not has_text:
        return False

    has_shading = bool(para_style.get("shading", {}).get("backgroundColor"))
    has_indent = bool(para_style.get("indentStart", {}).get("magnitude"))

    return all_monospace and (has_shading or has_indent)


def _extract_code_block_text(paragraph: dict) -> str:
    """Extract the code text from a code block paragraph, stripping markers."""
    parts = []
    for pe in paragraph.get("elements", []):
        if "textRun" in pe:
            content = pe["textRun"].get("content", "")
            cleaned = content.replace(CODE_BLOCK_MARKER, "")
            parts.append(cleaned)
    return "".join(parts).rstrip("\n")


def extract_text_from_elements(elements: list[dict], depth: int = 0) -> list[str]:
    """
    Extract text from document elements with full markdown formatting.

    Returns a list of lines (not joined) so callers can post-process.
    """
    global _inline_objects, _lists

    if depth > 5:
        return []

    lines: list[str] = []
    i = 0

    while i < len(elements):
        element = elements[i]

        if "paragraph" in element and _is_code_block_paragraph(element["paragraph"]):
            code_lines = []
            while (
                i < len(elements) and "paragraph" in elements[i] and _is_code_block_paragraph(elements[i]["paragraph"])
            ):
                code_text = _extract_code_block_text(elements[i]["paragraph"])
                code_lines.append(code_text)
                i += 1
            # Remove trailing empty lines from the code block
            while code_lines and not code_lines[-1].strip():
                code_lines.pop()
            if code_lines:
                lines.append("\n```\n")
                for cl in code_lines:
                    lines.append(cl + "\n")
                lines.append("```\n\n")
            continue

        if "paragraph" in element:
            paragraph = element["paragraph"]
            para_style = paragraph.get("paragraphStyle", {})
            named_style = para_style.get("namedStyleType", "NORMAL_TEXT")
            heading_prefix = HEADING_MAP.get(named_style, "")

            bullet = paragraph.get("bullet", None)
            list_prefix = ""
            if bullet:
                list_id = bullet.get("listId", "")
                nesting_level = bullet.get("nestingLevel", 0)
                indent = "  " * nesting_level

                glyph_type = ""
                if list_id in _lists:
                    list_props = _lists[list_id].get("listProperties", {})
                    nesting_levels = list_props.get("nestingLevels", [])
                    if nesting_level < len(nesting_levels):
                        glyph_type = nesting_levels[nesting_level].get("glyphType", "")
                        glyph_symbol = nesting_levels[nesting_level].get("glyphSymbol", "")
                        if glyph_symbol:
                            glyph_type = ""

                if glyph_type in ("DECIMAL", "ALPHA", "UPPER_ALPHA", "ROMAN", "UPPER_ROMAN"):
                    list_prefix = f"{indent}1. "
                else:
                    list_prefix = f"{indent}- "

            para_elements = paragraph.get("elements", [])
            current_line = ""

            for pe in para_elements:
                if "textRun" in pe:
                    current_line += _format_text_run(pe["textRun"])

                elif "inlineObjectElement" in pe:
                    obj_id = pe["inlineObjectElement"].get("inlineObjectId", "")
                    if obj_id and obj_id in _inline_objects:
                        obj = _inline_objects[obj_id]
                        embedded = obj.get("inlineObjectProperties", {}).get("embeddedObject", {})
                        image_uri = embedded.get("imageProperties", {}).get("contentUri", "")
                        description = embedded.get("description", "")
                        title = embedded.get("title", "image")

                        if image_uri:
                            local_path = download_image(image_uri, description)
                            if local_path:
                                alt_text = description or title or "image"
                                current_line += f"![{alt_text}]({local_path})"
                            else:
                                current_line += f"[Image: {title or 'embedded image'}]"
                        else:
                            current_line += "[Image: unable to extract]"

            line_text = current_line.rstrip("\n")

            if line_text.strip():
                if list_prefix:
                    lines.append(list_prefix + line_text + "\n")
                elif heading_prefix:
                    lines.append(heading_prefix + line_text + "\n")
                else:
                    lines.append(line_text + "\n")
            else:
                lines.append("\n")

        elif "table" in element:
            table = element["table"]
            table_rows = table.get("tableRows", [])

            for row_idx, row in enumerate(table_rows):
                row_cells = row.get("tableCells", [])
                cell_texts = []

                for cell in row_cells:
                    cell_content = cell.get("content", [])
                    cell_lines = extract_text_from_elements(cell_content, depth + 1)
                    cell_text = " ".join(line.strip() for line in cell_lines if line.strip())
                    cell_texts.append(cell_text)

                lines.append("| " + " | ".join(cell_texts) + " |\n")

                if row_idx == 0:
                    lines.append("|" + "|".join([" --- "] * len(cell_texts)) + "|\n")

            lines.append("\n")

        elif "sectionBreak" in element:
            lines.append("\n---\n\n")

        i += 1

    return lines


def process_tab(tab: dict, level: int = 0) -> str:
    global _inline_objects, _lists

    parts: list[str] = []

    if "documentTab" in tab:
        props = tab.get("tabProperties", {})
        tab_title = props.get("title", "Untitled Tab")

        indent = "  " * level
        parts.append(f"\n{indent}[Tab: {tab_title}]\n\n")

        doc_tab = tab.get("documentTab", {})
        _inline_objects.update(doc_tab.get("inlineObjects", {}))
        _lists.update(doc_tab.get("lists", {}))

        tab_body = doc_tab.get("body", {}).get("content", [])
        lines = extract_text_from_elements(tab_body)
        parts.extend(lines)

    for child_tab in tab.get("childTabs", []):
        parts.append(process_tab(child_tab, level + 1))

    return "".join(parts)


def fetch_document(doc_id: str, output_dir: Path | None = None) -> dict[str, Any]:
    global _inline_objects, _images_dir, _image_counter, _credentials, _lists

    _inline_objects = {}
    _lists = {}
    _image_counter = 0

    creds = get_credentials()
    _credentials = creds

    if output_dir:
        _images_dir = output_dir / "images"
        _images_dir.mkdir(parents=True, exist_ok=True)
    else:
        _images_dir = None

    docs_service = build("docs", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    file_metadata = (
        drive_service.files()
        .get(fileId=doc_id, fields="id, name, mimeType, modifiedTime, webViewLink", supportsAllDrives=True)
        .execute()
    )

    mime_type = file_metadata.get("mimeType", "")
    file_name = file_metadata.get("name", "Unknown")
    modified_time = file_metadata.get("modifiedTime", "")
    web_link = file_metadata.get("webViewLink", "")

    if mime_type == "application/vnd.google-apps.document":
        doc_data = docs_service.documents().get(documentId=doc_id, includeTabsContent=True).execute()

        _inline_objects.update(doc_data.get("inlineObjects", {}))
        _lists.update(doc_data.get("lists", {}))

        content_parts = []

        body_elements = doc_data.get("body", {}).get("content", [])
        main_lines = extract_text_from_elements(body_elements)
        main_content = "".join(main_lines)
        if main_content.strip():
            content_parts.append(main_content)

        for tab in doc_data.get("tabs", []):
            tab_content = process_tab(tab)
            if tab_content.strip():
                content_parts.append(tab_content)

        body_text = "\n".join(content_parts)
    else:
        body_text = f"[Unsupported document type: {mime_type}]"

    return {
        "metadata": {
            "title": file_name,
            "id": doc_id,
            "modified": modified_time,
            "link": web_link,
            "mimeType": mime_type,
        },
        "content": body_text,
        "images_downloaded": _image_counter,
    }


def format_output(doc: dict[str, Any]) -> str:
    meta = doc["metadata"]
    return f"""---
title: {meta["title"]}
id: {meta["id"]}
modified: {meta["modified"]}
link: {meta["link"]}
---

# {meta["title"]}

{doc["content"]}
"""


def main():
    if len(sys.argv) < 2:
        print("Usage: fetch_doc.py <doc_id_or_url> [output_file]")
        print()
        print("Fetches a Google Doc and converts to markdown with:")
        print("  - Headings (H1-H6)")
        print("  - Bold, italic, code, strikethrough")
        print("  - Bullet and numbered lists (nested)")
        print("  - Tables (markdown pipe format)")
        print("  - Links and images")
        print("  - Multi-tab documents")
        sys.exit(1)

    url_or_id = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    doc_id = extract_doc_id(url_or_id)
    print(f"Fetching document: {doc_id}", file=sys.stderr)

    try:
        output_dir = None
        if output_file:
            output_path = Path(output_file)
            output_dir = output_path.parent

        doc = fetch_document(doc_id, output_dir)
        output = format_output(doc)

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Saved to: {output_file}", file=sys.stderr)
            if doc.get("images_downloaded", 0) > 0:
                print(f"Images saved to: {output_dir}/images/", file=sys.stderr)
        else:
            print(output)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
