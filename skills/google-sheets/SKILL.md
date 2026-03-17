---
name: google-sheets
description: Read, write, and create Google Sheets. Use when the user asks to interact with Google Sheets, or when a workflow needs structured data persistence in a shared spreadsheet.
alwaysApply: false
globs:
---

# Google Sheets Skill

Python scripts for reading, writing, and creating Google Sheets with OAuth authentication.

## Prerequisites

**Python packages** (install once):
```bash
pip3 install google-auth google-auth-oauthlib google-api-python-client
```

**First-time auth**: On first script run, a browser window opens for Google OAuth consent. Grant spreadsheets + drive access. Token is cached locally in `scripts/secrets.json` (gitignored via `**/secrets.json`).

## Authentication

**OAuth credentials are baked into auth.py.** No setup required.

On first use (or if token expires), the script will:
1. Open a browser for OAuth consent
2. User grants spreadsheets + drive.file access
3. Token saved to `skills/google-sheets/scripts/secrets.json`

## Scripts

All scripts are located at `skills/google-sheets/scripts/` relative to the repo root.

### create_sheet.py

Create a new Google Sheet.

```bash
python3 skills/google-sheets/scripts/create_sheet.py "My Sheet" --columns "Name,Date,Status" --tabs "Data,Summary"
```

**Arguments:**
- `title`: Name for the new spreadsheet (required)
- `--columns`: Comma-separated column headers for the first row
- `--tabs`: Comma-separated tab names (default: Sheet1)
- `--json`: Output as JSON

### read_sheet.py

Read data from a Google Sheet.

```bash
python3 skills/google-sheets/scripts/read_sheet.py <sheet_id_or_url> --tab "Sheet1" --range "A1:D10"
```

**Arguments:**
- `sheet_id`: Spreadsheet ID or full URL (required)
- `--tab`: Tab name (default: Sheet1)
- `--range`: Cell range to read (default: entire tab)
- `--list-tabs`: List all tab names in the spreadsheet
- `--json`: Output as JSON

### write_sheet.py

Write data to a Google Sheet (append, update, or clear).

```bash
# Append rows
python3 skills/google-sheets/scripts/write_sheet.py <sheet_id> --tab "Sheet1" append '[["row1col1","row1col2"],["row2col1","row2col2"]]'

# Update specific cells
python3 skills/google-sheets/scripts/write_sheet.py <sheet_id> --tab "Sheet1" update "A1:B1" '[["new_val1","new_val2"]]'

# Clear a range
python3 skills/google-sheets/scripts/write_sheet.py <sheet_id> --tab "Sheet1" clear --range "A2:Z1000"
```

**Actions:**
- `append <json>`: Append rows to the end of a tab
- `update <range> <json>`: Overwrite specific cells
- `clear [--range R]`: Clear cells (entire tab if no range given)

## File Structure

```
skills/google-sheets/
├── SKILL.md
└── scripts/
    ├── auth.py
    ├── create_sheet.py
    ├── read_sheet.py
    ├── write_sheet.py
    ├── requirements.txt
    └── secrets.json      # Auto-generated on first use (gitignored via **/secrets.json)
```

## Required Scopes

- `https://www.googleapis.com/auth/spreadsheets`
- `https://www.googleapis.com/auth/drive.file`
