"""
Uses Claude Haiku 4.5 via kie.ai to compose a professional invoice email.

Usage:
    python tools/compose_email.py '<json_string>'

Output:
    JSON with keys: subject, body
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
        print("Usage: python tools/compose_email.py '<json_string>'", file=sys.stderr)
        sys.exit(1)

    data = json.loads(sys.argv[1])

    prompt = f"""Write a concise internal notification email to a billing team about a newly received invoice.
Rules:
- This is an internal email to the billing team, not to the client
- No salutation (do not start with "Dear" or "Hi")
- Include all invoice fields: invoice number, client name, client address, company name, total amount
- Keep it brief and factual — just the invoice details and a note that it has been logged
- Return ONLY valid JSON with exactly two keys: "subject" and "body"
- No markdown, no explanation

Invoice details:
Invoice Number: {data.get('invoice_number', '')}
Company Name: {data.get('company_name', '')}
Client Name: {data.get('client_name', '')}
Client Email: {data.get('client_email', '')}
Client Address: {data.get('client_address', '')}
Due Date: {data.get('due_date', '')}
Total Amount: {data.get('total_amount', '')}"""

    raw = call_haiku(prompt)

    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
