"""
Checks whether an invoice number already exists in the Google Sheet.

Usage:
    python tools/check_duplicate.py <invoice_number>

Exit codes:
    0 — not a duplicate (safe to proceed)
    1 — duplicate found (skip sheet update, notify billing team)

Output:
    Prints "duplicate" or "ok" to stdout.
"""

import os
import sys

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

SPREADSHEET_ID = os.getenv("SHEETS_ID")
SHEET_NAME = "Sheet1"
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.send",
]


def get_creds():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return creds


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/check_duplicate.py <invoice_number>", file=sys.stderr)
        sys.exit(2)

    invoice_number = sys.argv[1].strip()
    if not invoice_number:
        print("ok")
        sys.exit(0)

    creds = get_creds()
    service = build("sheets", "v4", credentials=creds)

    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A:A",
    ).execute()

    existing = [row[0].strip() for row in result.get("values", []) if row]

    if invoice_number in existing:
        print("duplicate")
        sys.exit(1)

    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
