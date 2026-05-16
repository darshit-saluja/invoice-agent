# Workflow: Process Invoice

## Objective
Automatically detect new invoice PDFs in Google Drive, extract structured data, record it in Google Sheets, and send a professional notification email to the client.

## Trigger
Run `tools/drive_monitor.py` to list unprocessed file IDs. Then run `tools/run_pipeline.py <file_id>` for each one. This can be scheduled via cron or Windows Task Scheduler to run hourly.

## Required Inputs
- `credentials.json` — Google OAuth client secrets (get from Google Cloud Console)
- `token.json` — Generated automatically on first run (OAuth browser flow)
- `KIE_API_KEY` in `.env` — kie.ai API key for Claude Haiku 4.5

## Tools (in execution order)

### Step 1 — Discover new files
```
python tools/drive_monitor.py
```
- Queries Drive folder `1wXh_wLgPiF8JHToRfgfdkkLrEN4YomuH` for PDFs
- Skips IDs already in `.tmp/processed_ids.txt`
- Prints one file ID per line

### Step 2 — For each file ID, run the pipeline
```
python tools/run_pipeline.py <file_id>
```
Internally runs steps 3–8 in sequence.

### Step 3 — Download
```
python tools/download_invoice.py <file_id>
```
- Downloads the PDF to `.tmp/<filename>.pdf`
- Prints the local path

### Step 4 — Extract text
```
python tools/extract_pdf_text.py <pdf_path>
```
- Uses `pdfplumber` to extract page text
- Writes to `.tmp/<filename>.txt`
- Prints the txt path

### Step 5 — Extract invoice data
```
python tools/extract_invoice_data.py <txt_path>
```
- Calls Claude Haiku 4.5 via kie.ai
- Endpoint: `POST https://api.kie.ai/claude/v1/messages`
- Extracts: `invoice_number`, `client_name`, `client_email`, `client_address`, `company_name`, `total_amount`
- Prints JSON to stdout

### Step 6 — Update Google Sheets
```
python tools/update_sheets.py '<json>'
```
- Appends a row to Sheet1 of spreadsheet `1vSfg2b8VQeoyEMh1kCt5xgP-jyf-zJrzWgvzp9zMXm0`
- Column order: invoice_number, client_name, client_email, client_address, company_name, total_amount

### Step 7 — Compose email
```
python tools/compose_email.py '<json>'
```
- Calls Claude Haiku 4.5 via kie.ai
- Returns JSON with `subject` and `body`
- Email has no salutation, includes all invoice fields

### Step 8 — Send email
```
python tools/send_email.py '{"to": "...", "subject": "...", "body": "..."}'
```
- Sends via Gmail API
- Recipient: `BILLING_TEAM_EMAIL` from `.env`

### Step 9 — Mark as processed
`run_pipeline.py` appends the file ID to `.tmp/processed_ids.txt` on success.

## Expected Outputs
- New row in Google Sheets with all 6 invoice fields
- Email delivered to the client

## Error Handling
- Any tool that fails will print to stderr and exit with code 1
- `run_pipeline.py` will halt the pipeline at the failing step and exit
- Re-running `run_pipeline.py` with the same file ID is safe — the file ID is only added to `processed_ids.txt` on full success
- If `pdfplumber` extracts no text (scanned image PDF), `extract_pdf_text.py` will produce an empty file; the LLM will return empty strings for all fields — check the sheet row and reprocess manually

## Edge Cases
- **Non-PDF files in folder**: `drive_monitor.py` filters by `mimeType='application/pdf'`
- **Scanned/image PDFs**: Text extraction will return empty; the pipeline will complete but data fields will be blank
- **Recipient address**: always read from `BILLING_TEAM_EMAIL` in `.env`
- **LLM returns markdown-wrapped JSON**: Both LLM tools strip triple-backtick fences before parsing
- **Token expiry**: All tools handle token refresh automatically via `google-auth`

## Scheduling (optional)
To run hourly on Windows, use Task Scheduler pointing to:
```
python tools/drive_monitor.py | ForEach-Object { python tools/run_pipeline.py $_ }
```
Or on Unix/Mac cron:
```
0 * * * * cd /path/to/INVOICE\ AGENT && python tools/drive_monitor.py | xargs -I{} python tools/run_pipeline.py {}
```
