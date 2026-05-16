# Invoice Agent

An automated invoice processing pipeline built on the **WAT framework** (Workflows, Agents, Tools). Monitors a Google Drive folder for new invoice PDFs, extracts structured data with an LLM, logs it to Google Sheets, and sends a notification email — all without manual intervention.

## How It Works

```
Google Drive (new PDF)
       │
       ▼
 drive_monitor.py       ← detects unprocessed invoices
       │
       ▼
 download_invoice.py    ← downloads PDF locally
       │
       ▼
 extract_pdf_text.py    ← pulls raw text via pdfplumber
       │
       ▼
extract_invoice_data.py ← Gemini 2.5 Flash extracts structured fields
       │
       ▼
  check_duplicate.py    ← checks Google Sheets for existing invoice number
       │
       ├─ duplicate → notify billing team → move to INVOICES FAILED
       │
       └─ new → send email → update Sheets → move to INVOICES PROCESSED
```

**Extracted fields:** Invoice Number, Client Name, Client Email, Client Address, Company Name, Total Amount

## Tech Stack

- **LLM:** Gemini 2.5 Flash via [kie.ai](https://kie.ai)
- **Storage:** Google Sheets (invoice database)
- **Trigger:** Google Drive folder watch
- **Email:** Gmail API
- **PDF parsing:** pdfplumber

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/darshit-saluja/invoice-agent.git
cd invoice-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Google Cloud setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create a project.
2. Enable these three APIs:
   - **Google Drive API**
   - **Google Sheets API**
   - **Gmail API**
3. Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**.
4. Set application type to **Desktop app**.
5. Download the JSON and save it as `credentials.json` in the project root.

### 4. Google Drive folders

Create three folders in Google Drive:
- `INVOICES` — drop new invoice PDFs here
- `INVOICES PROCESSED` — pipeline moves successfully processed files here
- `INVOICES FAILED` — pipeline moves duplicates or failed files here

To get a folder's ID: open the folder in Google Drive and copy the ID from the URL:
```
https://drive.google.com/drive/folders/<FOLDER_ID_IS_HERE>
```

### 5. Google Sheets database

Create a new Google Sheet with these columns in row 1 (exact names, in this order):

| Invoice Number | Client Name | Client Email | Client Address | Company Name | Total Amount |
|---|---|---|---|---|---|

Leave the sheet tab named **Sheet1** (default). Copy the spreadsheet ID from its URL:
```
https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID_IS_HERE>/edit
```

### 6. Configure environment variables

Create a `.env` file in the project root:

```env
# kie.ai API key (https://kie.ai)
KIE_API_KEY=your_kie_ai_api_key

# Email address that receives invoice notifications
BILLING_TEAM_EMAIL=billing@yourcompany.com

# Google Sheets spreadsheet ID (from the sheet URL)
SHEETS_ID=your_spreadsheet_id

# Google Drive folder IDs (from each folder's URL)
DRIVE_FOLDER_ID=your_invoices_folder_id
PROCESSED_FOLDER_ID=your_invoices_processed_folder_id
FAILED_FOLDER_ID=your_invoices_failed_folder_id
```

### 7. Authenticate with Google

Run any tool for the first time — a browser window will open asking you to sign in and grant permissions. This generates `token.json` automatically and won't prompt again:

```bash
python tools/drive_monitor.py
```

---

## Running the Pipeline

**Process all new invoices in the Drive folder:**

```bash
# Unix/macOS
python tools/drive_monitor.py | xargs -I{} python tools/run_pipeline.py {}

# Windows PowerShell
python tools/drive_monitor.py | ForEach-Object { python tools/run_pipeline.py $_ }
```

**Process a specific file by its Drive file ID:**

```bash
python tools/run_pipeline.py <google_drive_file_id>
```

---

## Scheduling (Optional)

**Windows Task Scheduler** — create a task that runs this command hourly:

```powershell
python tools/drive_monitor.py | ForEach-Object { python tools/run_pipeline.py $_ }
```

**Unix/macOS cron** — add to crontab (`crontab -e`):

```cron
0 * * * * cd /path/to/invoice-agent && python tools/drive_monitor.py | xargs -I{} python tools/run_pipeline.py {}
```

---

## Project Structure

```
tools/
├── drive_monitor.py        # Lists unprocessed Drive PDFs
├── download_invoice.py     # Downloads a PDF by file ID
├── extract_pdf_text.py     # Extracts text from PDF
├── extract_invoice_data.py # LLM-based field extraction
├── check_duplicate.py      # Checks Sheets for duplicate invoice number
├── update_sheets.py        # Appends row to Google Sheets
├── compose_email.py        # LLM-based email drafting
├── send_email.py           # Sends email via Gmail API
├── move_file.py            # Moves processed files in Drive
└── run_pipeline.py         # Orchestrates steps 2–9

workflows/
└── process_invoice.md      # Full pipeline SOP and edge case documentation

.env                        # API keys and config (gitignored — never commit this)
credentials.json            # Google OAuth client secrets (gitignored)
token.json                  # OAuth token, auto-generated (gitignored)
.tmp/                       # Temporary files, auto-generated (gitignored)
```

## WAT Framework

This project follows the **WAT architecture**:

- **Workflows** — Markdown SOPs in `workflows/` define what to do and how
- **Agents** — An LLM reads the workflow and orchestrates execution
- **Tools** — Python scripts in `tools/` do the actual deterministic work

This separation keeps AI reasoning focused on coordination while offloading execution to reliable, testable scripts.
