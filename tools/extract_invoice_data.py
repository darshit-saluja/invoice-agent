"""
Uses Claude Haiku 4.5 via kie.ai to extract structured fields from invoice text.

Usage:
    python tools/extract_invoice_data.py <txt_path>

Output:
    JSON string to stdout with keys:
    invoice_number, client_name, client_email, client_address, company_name, total_amount
"""

import json
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

KIE_URL = "https://api.kie.ai/claude/v1/messages"


def call_haiku(prompt: str) -> str:
    resp = requests.post(
        KIE_URL,
        headers={
            "Authorization": f"Bearer {os.getenv('KIE_API_KEY')}",
            "Content-Type": "application/json",
        },
        json={
            "model": "claude-haiku-4-5",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/extract_invoice_data.py <txt_path>", file=sys.stderr)
        sys.exit(1)

    txt_path = sys.argv[1]
    if not os.path.exists(txt_path):
        print(f"File not found: {txt_path}", file=sys.stderr)
        sys.exit(1)

    with open(txt_path, encoding="utf-8") as f:
        invoice_text = f.read()

    prompt = f"""Extract the following fields from this invoice text and return ONLY valid JSON with these exact keys:
invoice_number, company_name, client_name, client_email, client_address, due_date, total_amount

If a field is not found, use an empty string "".
For due_date, use the format YYYY-MM-DD if possible.
Do not include any explanation or markdown — return only the JSON object.

Invoice text:
{invoice_text}"""

    raw = call_haiku(prompt)

    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    data = json.loads(raw)
    print(json.dumps(data))


if __name__ == "__main__":
    main()
