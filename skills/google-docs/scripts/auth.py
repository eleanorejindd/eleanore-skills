#!/usr/bin/env python3
"""
Google OAuth authentication utilities for Google Docs/Drive access.

This module handles OAuth 2.0 authentication flow and token management.
"""

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.readonly",
]

# =============================================================================
# SECURITY NOTE: Why the client_secret is hardcoded here
# =============================================================================
# For Google OAuth "Desktop app" credentials, the client_secret is NOT actually
# secret. Google explicitly documents that desktop/native apps are "public clients"
# where the secret cannot be kept confidential (users can decompile/extract it).
#
# The security model for desktop OAuth relies on:
# 1. The user's explicit consent in the browser
# 2. The redirect URI validation (localhost only)
# 3. The authorization code exchange happening on the user's machine
#
# Many open-source tools (gcloud CLI, rclone, etc.) ship with embedded OAuth
# credentials for this reason.
#
# Reference: https://developers.google.com/identity/protocols/oauth2/native-app
# =============================================================================
DEFAULT_CLIENT_CONFIG = {
    "installed": {
        "client_id": "121795862047-kg2doo9rievlp82dc5skpgg5oufkfrs8.apps.googleusercontent.com",
        "client_secret": "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",
        "project_id": "adam-test-projects",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        # Google OAuth for desktop apps accepts http://localhost with any port.
        # Including variations for compatibility with different OAuth library behaviors.
        "redirect_uris": ["http://localhost", "http://localhost/", "urn:ietf:wg:oauth:2.0:oob"],
    }
}


def _default_token_path() -> str:
    """Return the default path for the cached OAuth token (secrets.json next to this file)."""
    return str(Path(__file__).resolve().parent / "secrets.json")


def get_credentials(token_path: str | None = None) -> Credentials:
    """
    Get valid Google API credentials, refreshing or creating as needed.

    Args:
        token_path: Path to token file (default: scripts/secrets.json)

    Returns:
        Valid Credentials object

    Raises:
        Exception: If authentication fails
    """
    if token_path is None:
        token_path = _default_token_path()

    creds = None

    # Load existing token if available
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            print(f"Warning: Could not load existing token: {e}")
            creds = None

    # Refresh or create new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Token refresh failed: {e}")
                creds = None

        if not creds:
            # Run OAuth flow using default config
            flow = InstalledAppFlow.from_client_config(DEFAULT_CLIENT_CONFIG, SCOPES)
            try:
                # port=0 lets OS pick an available port (avoids conflicts with 8080, etc.)
                # redirect_uri_trailing_slash=False avoids mismatch with URIs lacking trailing slash
                creds = flow.run_local_server(port=0, redirect_uri_trailing_slash=False)
            except Exception as e:
                error_msg = str(e).lower()
                if "redirect_uri_mismatch" in error_msg or "redirect" in error_msg:
                    raise Exception(
                        f"OAuth redirect_uri mismatch error: {e}\n\n"
                        "This usually means the OAuth client configuration doesn't match "
                        "Google Cloud Console settings. Please report this issue."
                    ) from e
                raise

        # Save token for next run
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())
            print(f"Token saved to {token_path}")

    return creds


def extract_doc_id(url_or_id: str) -> str:
    """
    Extract document ID from a Google Docs URL or return the ID if already provided.

    Args:
        url_or_id: Either a full Google Docs URL or just the document ID

    Returns:
        The document ID

    Examples:
        >>> extract_doc_id("1abc123xyz")
        "1abc123xyz"
        >>> extract_doc_id("https://docs.google.com/document/d/1abc123xyz/edit")
        "1abc123xyz"
    """
    import re

    # If it looks like a URL, extract the ID
    if "/" in url_or_id:
        # Match /d/{id}/ pattern
        match = re.search(r"/d/([a-zA-Z0-9_-]+)", url_or_id)
        if match:
            return match.group(1)

        # Match /document/{id} pattern
        match = re.search(r"/document/([a-zA-Z0-9_-]+)", url_or_id)
        if match:
            return match.group(1)

    # Assume it's already an ID
    return url_or_id
