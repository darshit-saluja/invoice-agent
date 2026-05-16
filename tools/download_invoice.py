"""
Downloads a Google Drive file by ID to .tmp/.

Usage:
    python tools/download_invoice.py <file_id>

Output:
    Prints the local path of the downloaded file to stdout.
"""

import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

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
        print("Usage: python tools/download_invoice.py <file_id>", file=sys.stderr)
        sys.exit(1)

    file_id = sys.argv[1]
    creds = get_creds()
    service = build("drive", "v3", credentials=creds)

    meta = service.files().get(fileId=file_id, fields="name").execute()
    filename = meta["name"]

    os.makedirs(".tmp", exist_ok=True)
    local_path = os.path.join(".tmp", filename)

    request = service.files().get_media(fileId=file_id)
    with open(local_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

    print(local_path)


if __name__ == "__main__":
    main()
