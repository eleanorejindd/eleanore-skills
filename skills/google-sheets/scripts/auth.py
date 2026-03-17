#!/usr/bin/env python3
"""Google OAuth authentication for Google Sheets/Drive access."""

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

# Desktop OAuth client credentials are public by design (see google-docs skill for rationale).
DEFAULT_CLIENT_CONFIG = {
    "installed": {
        "client_id": "121795862047-kg2doo9rievlp82dc5skpgg5oufkfrs8.apps.googleusercontent.com",
        "client_secret": "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",
        "project_id": "adam-test-projects",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "redirect_uris": [
            "http://localhost",
            "http://localhost/",
            "urn:ietf:wg:oauth:2.0:oob",
        ],
    }
}


def _default_token_path() -> str:
    """Return the default path for the cached OAuth token (secrets.json next to this file)."""
    return str(Path(__file__).resolve().parent / "secrets.json")


def get_credentials(token_path: str | None = None) -> Credentials:
    if token_path is None:
        token_path = _default_token_path()
    creds = None

    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            print(f"Warning: Could not load existing token: {e}")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            flow = InstalledAppFlow.from_client_config(DEFAULT_CLIENT_CONFIG, SCOPES)
            creds = flow.run_local_server(port=0, redirect_uri_trailing_slash=False)

        with open(token_path, "w") as f:
            f.write(creds.to_json())
            print(f"Token saved to {token_path}")

    return creds


def extract_sheet_id(url_or_id: str) -> str:
    """Extract spreadsheet ID from a Google Sheets URL or return the ID directly."""
    import re

    if "/" in url_or_id:
        match = re.search(r"/d/([a-zA-Z0-9_-]+)", url_or_id)
        if match:
            return match.group(1)
        match = re.search(r"/spreadsheets/([a-zA-Z0-9_-]+)", url_or_id)
        if match:
            return match.group(1)
    return url_or_id
