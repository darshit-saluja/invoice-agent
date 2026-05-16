"""
Sends an email via Gmail API.

Usage:
    python tools/send_email.py '<json_string>'

    JSON must have keys: to, subject, body
"""

import base64
import json
import os
import sys
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

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
        print("Usage: python tools/send_email.py '<json_string>'", file=sys.stderr)
        sys.exit(1)

    data = json.loads(sys.argv[1])
    to = data["to"]
    subject = data["subject"]
    body = data["body"]

    creds = get_creds()
    service = build("gmail", "v1", credentials=creds)

    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()

    service.users().messages().send(
        userId="me",
        body={"raw": encoded},
    ).execute()

    print(f"Email sent to {to}.")


if __name__ == "__main__":
    main()
