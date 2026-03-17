#!/usr/bin/env python3
"""
Append or replace content in a Google Doc.

Usage:
    python3 update_doc.py <doc_id_or_url> append <text>
    python3 update_doc.py <doc_id_or_url> append --file <path>
    python3 update_doc.py <doc_id_or_url> replace <old_text> <new_text>
    python3 update_doc.py <doc_id_or_url> insert-after-heading <heading_text> <content>
"""

import argparse
import json
import sys

from auth import extract_doc_id, get_credentials
from googleapiclient.discovery import build


def append_text(doc_id_or_url: str, text: str) -> dict:
    """Append text to the end of the document."""
    creds = get_credentials()
    service = build("docs", "v1", credentials=creds)
    doc_id = extract_doc_id(doc_id_or_url)

    doc = service.documents().get(documentId=doc_id).execute()
    body = doc.get("body", {})
    content = body.get("content", [])
    end_index = content[-1]["endIndex"] - 1 if content else 1

    requests = [{"insertText": {"location": {"index": end_index}, "text": text}}]

    service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

    return {"doc_id": doc_id, "action": "append", "chars_added": len(text)}


def replace_text(doc_id_or_url: str, old_text: str, new_text: str) -> dict:
    """Replace all occurrences of old_text with new_text."""
    creds = get_credentials()
    service = build("docs", "v1", credentials=creds)
    doc_id = extract_doc_id(doc_id_or_url)

    requests = [
        {
            "replaceAllText": {
                "containsText": {"text": old_text, "matchCase": True},
                "replaceText": new_text,
            }
        }
    ]

    result = service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

    replies = result.get("replies", [{}])
    occurrences = replies[0].get("replaceAllText", {}).get("occurrencesChanged", 0)
    return {"doc_id": doc_id, "action": "replace", "occurrences_changed": occurrences}


def insert_after_heading(doc_id_or_url: str, heading_text: str, content: str) -> dict:
    """Insert content after a specific heading (searches for the heading text in paragraphs)."""
    creds = get_credentials()
    service = build("docs", "v1", credentials=creds)
    doc_id = extract_doc_id(doc_id_or_url)

    doc = service.documents().get(documentId=doc_id).execute()
    body_content = doc.get("body", {}).get("content", [])

    insert_index = None
    for i, element in enumerate(body_content):
        if "paragraph" not in element:
            continue
        paragraph = element["paragraph"]
        para_text = ""
        for pe in paragraph.get("elements", []):
            if "textRun" in pe:
                para_text += pe["textRun"].get("content", "")

        if heading_text.strip().lower() in para_text.strip().lower():
            insert_index = element["endIndex"] - 1
            if i + 1 < len(body_content):
                insert_index = body_content[i + 1]["startIndex"]
            break

    if insert_index is None:
        return {"doc_id": doc_id, "action": "insert_after_heading", "error": f"Heading '{heading_text}' not found"}

    requests = [{"insertText": {"location": {"index": insert_index}, "text": content}}]

    service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

    return {"doc_id": doc_id, "action": "insert_after_heading", "heading": heading_text, "chars_added": len(content)}


def main():
    parser = argparse.ArgumentParser(description="Update a Google Doc")
    parser.add_argument("doc_id", help="Document ID or URL")

    sub = parser.add_subparsers(dest="action", required=True)

    append_p = sub.add_parser("append", help="Append text to end of doc")
    append_p.add_argument("text", nargs="?", help="Text to append")
    append_p.add_argument("--file", dest="file_path", help="Read text from file instead")

    replace_p = sub.add_parser("replace", help="Replace text in doc")
    replace_p.add_argument("old_text", help="Text to find")
    replace_p.add_argument("new_text", help="Replacement text")

    insert_p = sub.add_parser("insert-after-heading", help="Insert content after a heading")
    insert_p.add_argument("heading", help="Heading text to search for")
    insert_p.add_argument("content", help="Content to insert after the heading")

    args = parser.parse_args()

    if args.action == "append":
        if args.file_path:
            with open(args.file_path) as f:
                text = f.read()
        elif args.text:
            text = args.text
        else:
            print("Error: provide text or --file", file=sys.stderr)
            sys.exit(1)
        result = append_text(args.doc_id, text)
    elif args.action == "replace":
        result = replace_text(args.doc_id, args.old_text, args.new_text)
    elif args.action == "insert-after-heading":
        result = insert_after_heading(args.doc_id, args.heading, args.content)
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
