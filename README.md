# Robot Proactive Task and Constraints

Streamlit survey app for the HOI-SAN proactive robot task and navigation-constraint user study.

## Run locally

Prerequisite: install `uv` if you do not already have it.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Sync dependencies:

```bash
uv sync
```

Run the app:

```bash
uv run streamlit run streamlit_app.py
```

## Response storage

Real participant responses must be saved through a private Google Sheet backend before recruitment.

1. Create a private Google Sheet for responses.
2. Open `Extensions -> Apps Script`.
3. Paste `google_sheet_backend_apps_script.gs` into the Apps Script editor.
4. Deploy it as a Web App:
   - Execute as: `Me`
   - Who has access: `Anyone`
5. Copy the Web App URL into Streamlit Cloud secrets:

```toml
GOOGLE_SHEET_WEBHOOK_URL = "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec"
```

In real participant mode, the app will not show the Prolific completion link unless the response is saved successfully.
Researcher preview mode keeps responses in session only and is not for data collection.
