# BFL GST Invoice Validator — End-to-End Setup

Browser-based Streamlit app: users upload invoice PDFs, each file is sent
to the existing Vendor Invoice Validation Agent (Copilot Studio) through a
dedicated Power Automate flow, and results export to Excel. No Power
Platform environment access is required for end users — only the person
setting this up needs to build the flow once.

```
User → Streamlit App → Power Automate Flow → Copilot Studio Agent
                              ↓
                        Excel export
```

## Step 1 — Build the Power Automate flow

This is a new, dedicated flow, separate from any existing SharePoint-batch
flow. It receives one file at a time from Streamlit and calls your
existing agent.

1. **Create → Instant cloud flow** → trigger: **When an HTTP request is
   received**.
2. Click **Use sample payload to generate schema**, paste:
   ```json
   {
       "FileName": "sample.pdf",
       "FileContent": "base64string",
       "SharedSecret": "your-secret"
   }
   ```
3. Add a **Condition**: check `triggerBody()?['SharedSecret']` equals
   your configured secret. If not, **Terminate** the flow with status
   Failed.
4. Add **Execute Agent and wait**, select the Vendor Invoice Validation
   Agent.
   - Message: `Process this invoice`
   - Attachment: `base64ToBinary(triggerBody()?['FileContent'])`
5. Add **Compose** — Inputs = the agent's response text.
6. Add **Parse JSON** — Content = the Compose output, schema generated
   from a sample response.
7. Open the HTTP trigger's **Settings** and enable **Asynchronous Response**.
   Do not use the normal synchronous response for this flow. The initial
   response must be `202 Accepted` and include a `Location` header containing
   a URL that can be polled for the completed result. The final response at
   that URL must contain one output named `invoices`, whose value is the Parse
   JSON output's `invoices` array.
8. **Save**. Click the trigger again and copy the generated **HTTP URL**
   — this goes into `.env` in Step 2.

## Step 2 — Configure environment variables

Copy `.env.example` to `.env` and fill in real values (never commit this
file):

```
FLOW_HTTP_URL=https://your-flow-http-trigger-url
FLOW_SHARED_SECRET=some-random-secret-string
ACCESS_LIST_EMAILS=user1@bajajfinserv.in|user2@bajajfinserv.in
```

## Step 3 — Install dependencies

If the machine has internet access:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If the machine has **no internet access**, download the packages on a
different machine first, then transfer and install offline:

```cmd
mkdir packages
pip download -r requirements.txt -d packages
```

```powershell
python -m pip install --no-index --find-links="C:\path\to\packages" -r requirements.txt
```

## Step 4 — Test locally

```powershell
streamlit run app.py
```

Open the local URL, sign in with an email from `ACCESS_LIST_EMAILS`,
upload one test invoice, click **Validate Invoices**, confirm a row
appears with real extracted data, then confirm the Excel download works.

## Step 5 — Deploy for end users

Run bound to the network, not just localhost:

```powershell
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Users reach it at `http://<server-ip>:8501`. Confirm with IT/network that
inbound access to this port is allowed from wherever users connect
(internal network or VPN).

For a deployment that survives reboots and doesn't need a terminal left
open, run it as a scheduled task or Windows service instead of a manual
`streamlit run` session.

## Step 6 — Publish the code

```powershell
git init
git add .
git commit -m "Invoice validator wired to Copilot Studio agent"
git remote add origin <your-repo-url>
git push -u origin main
```

Make sure the GitHub repository is set to **private** (Settings → Danger
Zone → Change visibility) before pushing, since this handles BFL invoice
data and an internal flow endpoint.

## Project structure

```
invoice-ai-agent/
├── app.py                       # Main page: upload, access gate, results, download
├── app/
│   ├── config.py                 # Reads .env: flow URL, secret, access list
│   ├── exporter.py                # Builds the Excel output
│   ├── processor.py               # Per-file orchestration, fault isolation
│   ├── models.py                  # InvoiceRecord schema (30 output columns)
│   ├── extraction/
│   │   └── extractor.py           # Calls the flow, maps agent JSON to records
│   └── validation/
│       └── rules.py               # Light safety net (agent already validates)
├── requirements.txt
├── .gitignore
├── .env.example
└── .env                          # You create this locally — never committed
```

## Notes

- **PDF only.** The uploader accepts `.pdf` — image support (png/jpg) was
  removed until confirmed to work reliably with the agent's file-input
  handling.
- **One file at a time.** Each upload gets its own call to the flow —
  results appear in the table as soon as all uploads in the batch finish
  processing.
- **Large bundled files** (many invoices scanned into one very large PDF)
  can exceed what a single agent call handles reliably — this version
  does not pre-split such files. If that becomes a real need, the fix is
  a pre-processing step that detects invoice boundaries and splits the
  PDF before sending each piece to the agent.
