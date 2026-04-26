"""Google Calendar OAuth 2.0 authorization.

Usage (one-time):
    python -m cyber_persona.plugins.zectrix.calendar_sync.auth
"""

import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from cyber_persona.plugins.zectrix.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_SCOPES,
    TOKEN_PATH,
    ensure_data_dirs,
)

logger = logging.getLogger(__name__)


def load_credentials() -> Credentials | None:
    """Load existing credentials from token file."""
    if not TOKEN_PATH.exists():
        return None
    return Credentials.from_authorized_user_file(str(TOKEN_PATH), GOOGLE_SCOPES)


def save_credentials(creds: Credentials) -> None:
    """Save credentials to token file."""
    ensure_data_dirs()
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")


def get_valid_credentials() -> Credentials:
    """Get valid credentials, refreshing if necessary.

    If no credentials exist or they cannot be refreshed, raises an error
    instructing the user to run the auth flow first.
    """
    creds = load_credentials()

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_credentials(creds)
        return creds

    if creds and creds.valid:
        return creds

    # Need to run auth flow
    raise RuntimeError(
        "Google Calendar credentials not found or expired.\n"
        "Run: python -m cyber_persona.plugins.zectrix.calendar_sync.auth\n"
        f"Token will be saved to: {TOKEN_PATH}"
    )


def run_auth_flow() -> None:
    """Run the OAuth 2.0 authorization flow and save the token."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise RuntimeError(
            "ZECTRIX_GOOGLE_CLIENT_ID and ZECTRIX_GOOGLE_CLIENT_SECRET "
            "must be set in environment or .env file."
        )

    ensure_data_dirs()

    client_config = {
        "installed": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, GOOGLE_SCOPES)
    creds = flow.run_local_server(port=0)

    save_credentials(creds)
    logger.info("Authorization successful. Token saved to %s", TOKEN_PATH)
    print("\n✅ Authorization successful!")
    print(f"   Token saved to: {TOKEN_PATH}")
    print("   You can now run the sync scheduler.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_auth_flow()
