"""
Appends one invoice data row to Google Sheets.

Usage:
    python tools/update_sheets.py '<json_string>'

    The JSON must have keys:
    invoice_number, client_name, client_email, client_address, company_name, total_amount
"""

import json
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
        print("Usage: python tools/update_sheets.py '<json_string>'", file=sys.stderr)
        sys.exit(1)

    data = json.loads(sys.argv[1])
    row = [
        data.get("invoice_number", ""),
        data.get("company_name", ""),
        data.get("client_name", ""),
        data.get("client_email", ""),
        data.get("client_address", ""),
        data.get("due_date", ""),
        data.get("total_amount", ""),
    ]

    creds = get_creds()
    service = build("sheets", "v4", credentials=creds)

    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1",
        valueInputOption="RAW",
        body={"values": [row]},
    ).execute()

    print("Row appended to Google Sheets.")


if __name__ == "__main__":
    main()
