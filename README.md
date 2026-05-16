# Invoice Agent

An automated invoice processing pipeline built on the **WAT framework** (Workflows, Agents, Tools). Monitors a Google Drive folder for new invoice PDFs, extracts structured data with an LLM, logs it to Google Sheets, and sends a notification email — all without manual intervention.

## How It Works

```
Google Drive (new PDF)
       │
       ▼
 drive_monitor.py      ← detects unprocessed invoices
       │
       ▼
 download_invoice.py   ← downloads PDF locally
       │
       ▼
 extract_pdf_text.py   ← pulls raw text via pdfplumber
       │
       ▼
extract_invoice_data.py ← Gemini 2.5 Flash extracts structured fields
       │
       ▼
  update_sheets.py     ← appends row to Google Sheets
       │
       ▼
  compose_email.py     ← Gemini drafts a professional email
       │
       ▼
   send_email.py       ← delivers via Gmail API
```

**Extracted fields:** Invoice Number, Client Name, Client Email, Client Address, Company Name, Total Amount

## Tech Stack

- **LLM:** Gemini 2.5 Flash via [kie.ai](https://kie.ai)
- **Storage:** Google Sheets (as invoice DB)
- **Trigger:** Google Drive folder watch
- **Email:** Gmail API
- **PDF parsing:** pdfplumber

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/invoice-agent.git
cd invoice-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure credentials

Create a `.env` file:

```env
KIE_API_KEY=your_kie_ai_api_key
```

Place your `credentials.json` (Google OAuth client secrets from Google Cloud Console) in the project root.

On first run, a browser window will open for OAuth consent — this generates `token.json` automatically.

### 4. Google Cloud setup

Enable these APIs in your Google Cloud project:
- Google Drive API
- Google Sheets API
- Gmail API

### 5. Update resource IDs

In `workflows/process_invoice.md` and the relevant tool scripts, replace the placeholder folder/sheet IDs with your own:
- **Drive folder ID** — the folder to watch for new invoices
- **Sheets ID** — the spreadsheet to log invoice data

## Running the Pipeline

**Detect and process all new invoices:**

```bash
python tools/drive_monitor.py | xargs -I{} python tools/run_pipeline.py {}
```

**Process a specific file:**

```bash
python tools/run_pipeline.py <google_drive_file_id>
```

## Scheduling

**Windows Task Scheduler:**

```powershell
python tools/drive_monitor.py | ForEach-Object { python tools/run_pipeline.py $_ }
```

**Unix/macOS cron (hourly):**

```cron
0 * * * * cd /path/to/invoice-agent && python tools/drive_monitor.py | xargs -I{} python tools/run_pipeline.py {}
```

## Project Structure

```
tools/
├── drive_monitor.py        # Lists unprocessed Drive PDFs
├── download_invoice.py     # Downloads a PDF by file ID
├── extract_pdf_text.py     # Extracts text from PDF
├── extract_invoice_data.py # LLM-based field extraction
├── update_sheets.py        # Appends row to Google Sheets
├── compose_email.py        # LLM-based email drafting
├── send_email.py           # Sends email via Gmail API
├── move_file.py            # Moves processed files in Drive
├── check_duplicate.py      # Duplicate invoice detection
└── run_pipeline.py         # Orchestrates steps 2–8

workflows/
└── process_invoice.md      # SOP: full pipeline documentation

.tmp/                       # Temporary files (gitignored)
.env                        # API keys (gitignored)
credentials.json            # Google OAuth secrets (gitignored)
token.json                  # OAuth token (gitignored)
```

## WAT Framework

This project follows the **WAT architecture**:

- **Workflows** — Markdown SOPs in `workflows/` define what to do and how
- **Agents** — An LLM reads the workflow and orchestrates execution
- **Tools** — Python scripts in `tools/` do the actual deterministic work

This separation keeps AI reasoning focused on coordination while offloading execution to reliable, testable scripts.
