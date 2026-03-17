---
name: google-docs
description: Read, write, and search Google Docs. Use when the user asks to interact with Google Docs, or mentions a Google Docs URL or document ID.
alwaysApply: false
globs:
---

# Google Docs Skill

Python scripts for reading and writing Google Docs with OAuth authentication.

## Prerequisites

**Python packages** (install once):
```bash
pip3 install google-auth google-auth-oauthlib google-api-python-client requests
```

**First-time auth**: On first script run, a browser window opens for Google OAuth consent. Grant read+write access to Docs/Drive. Token is cached locally in `scripts/secrets.json` (gitignored via `**/secrets.json`).

## Scripts

All scripts are located at `skills/google-docs/scripts/` relative to the repo root.

### fetch_doc.py -- Read a doc as markdown

Fetches a Google Doc and converts to markdown preserving all formatting.

```bash
python3 skills/google-docs/scripts/fetch_doc.py <doc_id_or_url> [output_file]
```

**Formatting preserved:**

| Google Docs Format | Markdown Output |
|---|---|
| Heading 1-6 | `#` through `######` |
| Bold | `**text**` |
| Italic | `*text*` |
| Bold+Italic | `***text***` |
| Strikethrough | `~~text~~` |
| Monospace font (Courier New, Consolas, etc.) | `` `code` `` |
| Hyperlinks | `[text](url)` |
| Bullet lists (nested) | `- item` / `  - nested` |
| Numbered lists (nested) | `1. item` / `  1. nested` |
| Tables | Markdown pipe tables with `---` separator |
| Images | `![alt](images/image_001.png)` (downloaded) |
| Multi-tab docs | `[Tab: Name]` headers |
| Section breaks | `---` |

**Examples:**
```bash
# Fetch to stdout
python3 skills/google-docs/scripts/fetch_doc.py 1abc123xyz

# Using full URL
python3 skills/google-docs/scripts/fetch_doc.py "https://docs.google.com/document/d/1abc123xyz/edit"

# Save to file (images download to ./images/)
python3 skills/google-docs/scripts/fetch_doc.py 1abc123xyz ./output.md
```

**Output format:**
```markdown
---
title: Document Title
id: 1abc123xyz
modified: 2025-01-15T10:30:00Z
link: https://docs.google.com/document/d/1abc123xyz/edit
---

# Document Title

[Tab: Main Content]

## Section Heading

Regular text with **bold** and *italic* and `code`.

- Bullet one
- Bullet two

| Header | Value |
| --- | --- |
| Row 1 | Data |
```

### format_doc.py -- Write formatted content

Insert headings, tables, code blocks, and lists with proper Google Docs formatting. Inserts at end of doc by default, or after a specific heading with `--after`.

```bash
# Insert a heading (levels 1-6)
python3 skills/google-docs/scripts/format_doc.py <doc_id> heading 2 "My Section Title"

# Insert a table (first row = bold headers)
python3 skills/google-docs/scripts/format_doc.py <doc_id> table '[["Service","Count"],["USF","5"],["ETL2.0","3"]]'

# Insert a code block (monospace, gray background, indented)
python3 skills/google-docs/scripts/format_doc.py <doc_id> code "SELECT * FROM users WHERE active = true"

# Insert a bullet list
python3 skills/google-docs/scripts/format_doc.py <doc_id> bullets '["First item","Second item","Third item"]'

# Insert a numbered list
python3 skills/google-docs/scripts/format_doc.py <doc_id> numbered '["Step one","Step two","Step three"]'

# Insert markdown (auto-parses headings, lists, tables, code blocks)
python3 skills/google-docs/scripts/format_doc.py <doc_id> markdown --file ./content.md
python3 skills/google-docs/scripts/format_doc.py <doc_id> markdown "## Title\n\n- bullet one\n- bullet two"

# Insert after a specific heading instead of at the end
python3 skills/google-docs/scripts/format_doc.py <doc_id> --after "Background" table '[["Col1","Col2"],["a","b"]]'
```

**Formatting applied by each command:**

| Command | Google Docs Formatting |
|---|---|
| `heading` | Named style (HEADING_1 through HEADING_6) |
| `table` | Native table, first row bold |
| `code` | Courier New 10pt, gray background, indented (styled, not native -- API limitation) |
| `bullets` | Native bullet list (disc/circle/square nesting) |
| `numbered` | Native numbered list (decimal/alpha/roman nesting) |
| `markdown` | Auto-detects all of the above from markdown syntax |

### update_doc.py -- Plain text operations

Append, replace, or insert plain text.

```bash
# Append text to end of doc
python3 skills/google-docs/scripts/update_doc.py <doc_id> append "New text to add"

# Append from file
python3 skills/google-docs/scripts/update_doc.py <doc_id> append --file ./content.md

# Replace all occurrences
python3 skills/google-docs/scripts/update_doc.py <doc_id> replace "old text" "new text"

# Insert after a heading
python3 skills/google-docs/scripts/update_doc.py <doc_id> insert-after-heading "Background" "Content here"
```

### search_docs.py -- Find docs by name

```bash
python3 skills/google-docs/scripts/search_docs.py "quarterly review" --limit 5
python3 skills/google-docs/scripts/search_docs.py "design doc" --json
```

## File Structure

```
skills/google-docs/
├── SKILL.md
└── scripts/
    ├── auth.py           # OAuth with baked-in credentials
    ├── fetch_doc.py      # Read doc → markdown (headings, lists, tables, code, images)
    ├── format_doc.py     # Write formatted content (headings, tables, code, lists, markdown)
    ├── update_doc.py     # Plain text append/replace/insert
    ├── search_docs.py    # Search by name
    ├── requirements.txt
    └── secrets.json      # Auto-generated user token (gitignored via **/secrets.json)
```

## Known Limitations

- **Code blocks (write)**: The Google Docs API cannot create native code blocks (the kind triggered by ``` in the UI). `format_doc.py code` creates styled blocks (Courier New + gray background) which look similar but aren't structurally identical. Native code blocks can only be created manually in the Google Docs UI.
- **Code blocks (read)**: `fetch_doc.py` correctly reads both native code blocks and styled code blocks as fenced markdown code blocks.

## Required Scopes

- `https://www.googleapis.com/auth/documents` (read+write)
- `https://www.googleapis.com/auth/drive.readonly` (read file metadata, search)
