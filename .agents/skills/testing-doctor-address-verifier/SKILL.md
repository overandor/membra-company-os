---
name: testing-doctor-address-verifier
description: Test the Doctor Address Verifier Flask app end-to-end. Use when verifying changes to the doctor-address-verifier UI, API, or verification engine.
---

# Testing the Doctor Address Verifier

## Quick Start

```bash
cd 02_AI_Agents/doctor-address-verifier
pip install -r requirements.txt
NO_OLLAMA=1 python app.py  # starts on port 5001
```

The app runs at `http://127.0.0.1:5001`. Use `NO_OLLAMA=1` for rule-based verification (no local LLM needed).

## Key Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Web UI with upload zone |
| `/upload` | POST | Upload Excel file, starts background verification job |
| `/status/<job_id>` | GET | Poll job progress (status, current doctor, total) |
| `/download/<job_id>` | GET | Download verified spreadsheet |
| `/api/verify` | POST | Single-doctor verification via JSON |

## API Test Patterns

### Known NPPES Match (expect EXTERNALLY SUPPORTED / High)
Use a doctor whose NPPES practice address matches. Example:
```bash
curl -X POST http://127.0.0.1:5001/api/verify \
  -H "Content-Type: application/json" \
  -d '{"name": "AASHAT, SUPREET", "address": "111 E 210TH ST", "city": "BRONX", "state": "NY", "zip": "10467"}'
```
Expect: `visit_readiness`="EXTERNALLY SUPPORTED", `confidence`="High", `verification_method` contains "NPPES-MATCH" and "MONTEFIORE-CAMPUS".

**Important**: Not all doctors at 111 E 210th St will return NPPES-MATCH — many have different practice addresses in NPPES. Verify your test doctor's NPPES record first via `https://npiregistry.cms.hhs.gov/api/?version=2.1&first_name=SUPREET&last_name=AASHAT&state=NY`.

### Fake Doctor (expect REVIEW / Low)
```bash
curl -X POST http://127.0.0.1:5001/api/verify \
  -H "Content-Type: application/json" \
  -d '{"name": "ZZZZNOTREAL, XXXXXFAKE", "address": "999 NOWHERE ST", "city": "BRONX", "state": "NY", "zip": "10467"}'
```
Expect: `visit_readiness`="REVIEW - no NPPES record", `confidence`="Low", `verification_method`="NPPES-NOT-FOUND".

### Error Handling
- Missing `name` field → HTTP 400, `{"error": "Provide at least 'name' field"}`
- Upload non-Excel file → HTTP 400, `{"error": "Please upload an Excel (.xlsx) or CSV file"}`

## UI Upload Test

1. Create a small test Excel with columns: `Doctor Name`, `Address`, `City`, `State`, `Zip`
2. Use "LASTNAME, FIRSTNAME" format for doctor names
3. Navigate to `http://127.0.0.1:5001/`, click upload zone, select file
4. Click "Verify Addresses" — button only enables after file selection
5. Watch progress bar fill, then verify Results stat cards appear
6. Click "Download Verified Spreadsheet" — verify output has "Summary" and "Doctor Verification Worklist" sheets

## Output Verification

The downloaded Excel should contain these 15 evidence columns:
`Visit Readiness`, `Confidence`, `Verification_Method`, `External Evidence Note`, `NPPES_Address`, `Corrected Address`, `Routing Action`, `NPPES_Link`, `Hospital_Page_Link`, `Doximity_Link`, `WebMD_Link`, `Healthgrades_Link`, `Google_Maps_Link`, `All_Evidence_Links`, `LLM_Analysis`

## Hospital System Detection

The app auto-detects known hospital addresses. Key patterns:
- `111 E 210` → Montefiore Moses Campus
- `3444 KOSSUTH` → Montefiore Family Care Center
- `1400 PELHAM` → Jacobi Medical Center
- `3415 BAINBRIDGE` → CHAM / Montefiore
- `1650 GRAND` → BronxCare Health System

## Gotchas

- The NPPES API is live and rate-limited. The app sleeps 0.3s between doctors. Large uploads (100+ doctors) take minutes.
- Browser file dialog on Windows may need Desktop or Downloads as the navigation target. Copy test files there first.
- When navigating to localhost:5001 in the browser, use `window.location.href = 'http://127.0.0.1:5001/'` via console if the address bar mangles the URL.
- The `column_map` auto-detection looks for "doctor" or "name" in column headers (case-insensitive). Use "Doctor Name" for reliable detection.
