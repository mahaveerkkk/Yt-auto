#!/usr/bin/env python3
"""
YouTube OAuth Channel Authenticator for AutoDirector.
Run this ONCE to authenticate your YouTube channel.
Select your new Brand Channel when prompted!
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from google_auth_oauthlib.flow import InstalledAppFlow
from config.settings import settings
from utils.logger import logger

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]
CLIENT_SECRETS_FILE = BASE_DIR / "config" / "client_secrets.json"
TOKEN_FILE = BASE_DIR / "config" / "youtube_token.json"


def authenticate():
    if not CLIENT_SECRETS_FILE.exists():
        logger.error(f"client_secrets.json not found at {CLIENT_SECRETS_FILE}")
        return False

    logger.info("Starting YouTube Channel Authorization Flow...")
    print("\n" + "=" * 60)
    print("🔑 YOUTUBE CHANNEL AUTHORIZATION")
    print("=" * 60)
    print("Opening local browser for Google authorization...")
    print("NOTE: When Google asks 'Choose an account or Brand Account',")
    print("select your newly created Brand Channel!\n")

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_SECRETS_FILE), scopes=SCOPES
        )
        # Try local server first (works on desktop / Pi with browser)
        # port=8080 or port=0
        creds = flow.run_local_server(port=8080, open_browser=True, prompt="consent")

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

        print("\n" + "=" * 60)
        print("🎉 SUCCESS! YouTube channel authenticated successfully!")
        print(f"Token saved to: {TOKEN_FILE}")
        print("Now AutoDirector can upload videos 100% autonomously!")
        print("=" * 60 + "\n")
        return True
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        print(f"\n❌ Error during auth: {e}")
        return False


if __name__ == "__main__":
    authenticate()
