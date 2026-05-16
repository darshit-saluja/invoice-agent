"""
Moves a Google Drive file from its current parent to a target folder.

Usage:
    python tools/move_file.py <file_id> <target_folder_id>
"""

import os
import sys

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

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
    if len(sys.argv) < 3:
        print("Usage: python tools/move_file.py <file_id> <target_folder_id>", file=sys.stderr)
        sys.exit(1)

    file_id = sys.argv[1]
    target_folder_id = sys.argv[2]

    creds = get_creds()
    service = build("drive", "v3", credentials=creds)

    file_meta = service.files().get(fileId=file_id, fields="parents").execute()
    current_parents = ",".join(file_meta.get("parents", []))

    service.files().update(
        fileId=file_id,
        addParents=target_folder_id,
        removeParents=current_parents,
        fields="id, parents",
    ).execute()

    print(f"Moved {file_id} to folder {target_folder_id}.")


if __name__ == "__main__":
    main()
