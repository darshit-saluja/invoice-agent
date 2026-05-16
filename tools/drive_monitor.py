"""
Lists new PDF files in the watched Google Drive folder that haven't been processed yet.
Processed file IDs are tracked in .tmp/processed_ids.txt.

Usage:
    python tools/drive_monitor.py

Output:
    One file ID per line (stdout). Empty output means no new files.
"""

import os

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
PROCESSED_IDS_FILE = ".tmp/processed_ids.txt"
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


def load_processed_ids():
    os.makedirs(".tmp", exist_ok=True)
    if not os.path.exists(PROCESSED_IDS_FILE):
        return set()
    with open(PROCESSED_IDS_FILE) as f:
        return {line.strip() for line in f if line.strip()}


def main():
    creds = get_creds()
    service = build("drive", "v3", credentials=creds)

    results = service.files().list(
        q=f"'{FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false",
        fields="files(id, name)",
    ).execute()

    files = results.get("files", [])
    processed = load_processed_ids()
    new_files = [f for f in files if f["id"] not in processed]

    for f in new_files:
        print(f["id"])


if __name__ == "__main__":
    main()
