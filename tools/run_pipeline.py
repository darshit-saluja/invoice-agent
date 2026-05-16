"""
Orchestrates the full invoice processing pipeline for a single Drive file ID.

Usage:
    python tools/run_pipeline.py <file_id>

Flow:
    1. Download invoice from Drive
    2. Extract text from PDF
    3. Extract structured data via Gemini 2.5 Flash
    4. Check for duplicate invoice number in Google Sheets
       - Duplicate: notify billing team → move to INVOICES FAILED
       - Not duplicate: send details email → update Sheets → move to INVOICES PROCESSED
    5. Mark Drive file ID as processed
"""

import json
import os
import subprocess
import sys

from dotenv import load_dotenv

load_dotenv()

PROCESSED_IDS_FILE = ".tmp/processed_ids.txt"


def run(cmd: list[str], allowed_exit_codes: list[int] = None) -> tuple[str, int]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    allowed = allowed_exit_codes or [0]
    if result.returncode not in allowed:
        print(f"[ERROR] Command failed: {' '.join(cmd)}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip(), result.returncode


def move_file(file_id: str, folder_env_key: str):
    folder_id = os.getenv(folder_env_key)
    run(["python", "tools/move_file.py", file_id, folder_id])


def send_email(subject: str, body: str):
    recipient = os.getenv("BILLING_TEAM_EMAIL")
    payload = json.dumps({"to": recipient, "subject": subject, "body": body})
    run(["python", "tools/send_email.py", payload])
    print(f"      Email sent to {recipient}.")


def mark_processed(file_id: str):
    os.makedirs(".tmp", exist_ok=True)
    with open(PROCESSED_IDS_FILE, "a") as f:
        f.write(file_id + "\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/run_pipeline.py <file_id>", file=sys.stderr)
        sys.exit(1)

    file_id = sys.argv[1]

    try:
        print(f"[1/4] Downloading invoice {file_id}...")
        pdf_path, _ = run(["python", "tools/download_invoice.py", file_id])
        print(f"      Saved to {pdf_path}")

        print("[2/4] Extracting text from PDF...")
        txt_path, _ = run(["python", "tools/extract_pdf_text.py", pdf_path])
        print(f"      Text at {txt_path}")

        print("[3/4] Extracting invoice data via Gemini 2.5 Flash...")
        invoice_json, _ = run(["python", "tools/extract_invoice_data.py", txt_path])
        invoice_data = json.loads(invoice_json)
        print(f"      Data: {invoice_json}")

        invoice_number = invoice_data.get("invoice_number", "")

        print("[4/4] Checking for duplicate...")
        _, exit_code = run(
            ["python", "tools/check_duplicate.py", invoice_number],
            allowed_exit_codes=[0, 1],
        )

        if exit_code == 1:
            print(f"      Duplicate: invoice {invoice_number}. Notifying billing team.")
            send_email(
                subject=f"Duplicate Invoice Received: {invoice_number}",
                body=f"Invoice {invoice_number} has already been recorded. No action taken.",
            )
            move_file(file_id, "FAILED_FOLDER_ID")
            mark_processed(file_id)
            print("Done. Duplicate invoice moved to INVOICES FAILED.")
            return

        print("      No duplicate. Notifying billing team...")
        email_json, _ = run(["python", "tools/compose_email.py", invoice_json])
        email_data = json.loads(email_json)
        send_email(subject=email_data["subject"], body=email_data["body"])

        print("      Updating Google Sheets...")
        run(["python", "tools/update_sheets.py", invoice_json])
        print("      Sheet updated.")

        move_file(file_id, "PROCESSED_FOLDER_ID")
        mark_processed(file_id)
        print(f"Done. Invoice {invoice_number} moved to INVOICES PROCESSED.")

    except SystemExit:
        print(f"[FAIL] Pipeline error on {file_id}. Moving to INVOICES FAILED.", file=sys.stderr)
        mark_processed(file_id)
        move_file(file_id, "FAILED_FOLDER_ID")
        sys.exit(1)


if __name__ == "__main__":
    main()
