"""
Doctor Address Verifier — Flask web application.
Upload a doctor worklist, verify addresses via NPPES + web crawling + Ollama,
download results.
"""

import os
import sys
import json
import uuid
import threading
import time
from pathlib import Path

# Ensure the package directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file

from verifier import verify_doctor, check_ollama_status

app = Flask(__name__)

UPLOAD_DIR = Path("uploads")
RESULTS_DIR = Path("results")
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# Ollama config
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
NO_OLLAMA = os.environ.get("NO_OLLAMA", "").strip() == "1"
ENABLE_CRAWLING = os.environ.get("NO_CRAWLING", "").strip() != "1"

# In-memory job tracker
jobs = {}


def run_verification(job_id, filepath):
    """Background thread that processes the uploaded spreadsheet."""
    job = jobs[job_id]
    job["status"] = "running"
    job["message"] = "Reading spreadsheet..."

    try:
        # Try to find a sheet with doctor data
        xls = pd.ExcelFile(filepath)
        df = None
        for sheet in xls.sheet_names:
            candidate = pd.read_excel(filepath, sheet_name=sheet)
            cols_lower = [c.lower() for c in candidate.columns]
            if any("doctor" in c or "name" in c for c in cols_lower):
                df = candidate
                job["sheet_name"] = sheet
                break

        if df is None:
            df = pd.read_excel(filepath, sheet_name=0)
            job["sheet_name"] = xls.sheet_names[0]

        # Detect column mapping
        col_map = {}
        for c in df.columns:
            cl = c.lower().strip()
            if "doctor" in cl or cl == "name" or cl == "provider name":
                col_map["name"] = c
            elif cl in ("address", "street", "address_1", "street address"):
                col_map["address"] = c
            elif cl == "city":
                col_map["city"] = c
            elif cl == "state":
                col_map["state"] = c
            elif cl in ("zip", "zipcode", "zip code", "postal code"):
                col_map["zip"] = c
            elif "specialty" in cl or "speciality" in cl:
                col_map["specialty"] = c

        if "name" not in col_map:
            job["status"] = "error"
            job["message"] = (
                "Could not find a 'Doctor Name' or 'Name' column. "
                f"Found columns: {list(df.columns)}"
            )
            return

        total = len(df)
        job["total"] = total
        crawl_label = "with web crawling" if ENABLE_CRAWLING else "rule-based"
        llm_label = "with Ollama LLM" if not NO_OLLAMA else ""
        job["message"] = (
            f"Starting verification of {total} doctors "
            f"({crawl_label}{', ' + llm_label if llm_label else ''})..."
        )

        # Add result columns
        new_cols = [
            "Visit Readiness", "Confidence", "Verification_Method",
            "External Evidence Note", "NPPES_Address", "Corrected Address",
            "Routing Action", "NPPES_Link", "Hospital_Page_Link",
            "Doximity_Link", "WebMD_Link", "Healthgrades_Link",
            "Google_Maps_Link", "All_Evidence_Links", "LLM_Analysis",
            "Crawl_Sources_Checked", "Crawl_Sources_Confirmed",
            "Crawl_Evidence",
        ]
        for col in new_cols:
            if col not in df.columns:
                df[col] = ""

        for idx, row in df.iterrows():
            doctor = {
                "name": str(row.get(col_map.get("name", ""), "")),
                "address": str(row.get(col_map.get("address", ""), "")),
                "city": str(row.get(col_map.get("city", ""), "")),
                "state": str(row.get(col_map.get("state", ""), "NY")),
                "zip": str(row.get(col_map.get("zip", ""), "")),
            }

            if not doctor["name"] or doctor["name"] == "nan":
                continue

            job["current"] = idx + 1
            job["current_doctor"] = doctor["name"]
            job["message"] = f"Verifying {idx + 1}/{total}: {doctor['name']}"

            result = verify_doctor(
                doctor,
                ollama_host=OLLAMA_HOST,
                ollama_model=OLLAMA_MODEL,
                use_ollama=not NO_OLLAMA,
                enable_crawling=ENABLE_CRAWLING,
            )

            # Map results to dataframe
            df.at[idx, "Visit Readiness"] = result["visit_readiness"]
            df.at[idx, "Confidence"] = result["confidence"]
            df.at[idx, "Verification_Method"] = result["verification_method"]
            df.at[idx, "External Evidence Note"] = result["evidence_note"]
            df.at[idx, "NPPES_Address"] = result["nppes_address"]
            df.at[idx, "Corrected Address"] = result["corrected_address"]
            df.at[idx, "Routing Action"] = result["routing_action"]
            df.at[idx, "NPPES_Link"] = result["nppes_link"]
            df.at[idx, "Hospital_Page_Link"] = result["hospital_page_link"]
            df.at[idx, "Doximity_Link"] = result["doximity_link"]
            df.at[idx, "WebMD_Link"] = result["webmd_link"]
            df.at[idx, "Healthgrades_Link"] = result["healthgrades_link"]
            df.at[idx, "Google_Maps_Link"] = result["google_maps_link"]
            df.at[idx, "All_Evidence_Links"] = result["all_evidence_links"]
            df.at[idx, "LLM_Analysis"] = result["llm_analysis"]
            df.at[idx, "Crawl_Sources_Checked"] = result.get(
                "crawl_sources_checked", 0
            )
            df.at[idx, "Crawl_Sources_Confirmed"] = result.get(
                "crawl_sources_confirmed", 0
            )
            df.at[idx, "Crawl_Evidence"] = result.get("crawl_evidence", "")

            # Rate limit
            time.sleep(0.3)

        # Save output
        output_path = RESULTS_DIR / f"verified_{job_id}.xlsx"
        with pd.ExcelWriter(str(output_path), engine="openpyxl") as writer:
            supported = len(
                df[df["Visit Readiness"] == "EXTERNALLY SUPPORTED"]
            )
            review = len(
                df[df["Visit Readiness"].str.contains("REVIEW", na=False)]
            )
            summary = pd.DataFrame({
                "Metric": [
                    "Total doctors", "EXTERNALLY SUPPORTED",
                    "REVIEW (various)", "High confidence",
                    "Medium confidence", "Low confidence",
                ],
                "Value": [
                    total, supported, review,
                    len(df[df["Confidence"] == "High"]),
                    len(df[df["Confidence"] == "Medium"]),
                    len(df[df["Confidence"] == "Low"]),
                ],
            })
            summary.to_excel(writer, sheet_name="Summary", index=False)
            df.to_excel(
                writer, sheet_name="Doctor Verification Worklist", index=False
            )

        job["status"] = "complete"
        job["output_file"] = str(output_path)
        job["message"] = (
            f"Done! {supported} supported, {review} need review out of {total}."
        )
        job["summary"] = {
            "total": total,
            "supported": supported,
            "review": review,
            "high_conf": int((df["Confidence"] == "High").sum()),
            "medium_conf": int((df["Confidence"] == "Medium").sum()),
            "low_conf": int((df["Confidence"] == "Low").sum()),
        }

    except Exception as e:
        job["status"] = "error"
        job["message"] = f"Error: {str(e)}"
        import traceback
        job["traceback"] = traceback.format_exc()


@app.route("/")
def index():
    return render_template(
        "index.html",
        ollama_model=OLLAMA_MODEL,
        no_ollama=NO_OLLAMA,
        enable_crawling=ENABLE_CRAWLING,
    )


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.endswith((".xlsx", ".xls", ".csv")):
        return jsonify({"error": "Please upload an Excel (.xlsx) or CSV file"}), 400

    job_id = str(uuid.uuid4())[:8]
    filepath = UPLOAD_DIR / f"{job_id}_{file.filename}"
    file.save(str(filepath))

    jobs[job_id] = {
        "id": job_id,
        "filename": file.filename,
        "filepath": str(filepath),
        "status": "queued",
        "message": "Queued for processing...",
        "total": 0,
        "current": 0,
        "current_doctor": "",
    }

    thread = threading.Thread(target=run_verification, args=(job_id, str(filepath)))
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id, "status": "queued"})


@app.route("/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify({
        "id": job["id"],
        "status": job["status"],
        "message": job["message"],
        "total": job.get("total", 0),
        "current": job.get("current", 0),
        "current_doctor": job.get("current_doctor", ""),
        "summary": job.get("summary"),
    })


@app.route("/download/<job_id>")
def download(job_id):
    job = jobs.get(job_id)
    if not job or job["status"] != "complete":
        return jsonify({"error": "Results not ready"}), 404

    return send_file(
        job["output_file"],
        as_attachment=True,
        download_name=f"verified_{job.get('filename', 'results.xlsx')}",
    )


@app.route("/api/verify", methods=["POST"])
def api_verify_single():
    """API endpoint to verify a single doctor."""
    data = request.json
    if not data or "name" not in data:
        return jsonify({"error": "Provide at least 'name' field"}), 400

    result = verify_doctor(
        data,
        ollama_host=OLLAMA_HOST,
        ollama_model=OLLAMA_MODEL,
        use_ollama=not NO_OLLAMA,
        enable_crawling=ENABLE_CRAWLING,
    )
    return jsonify(result)


@app.route("/api/ollama-status")
def ollama_status():
    """Check Ollama status and available models."""
    status = check_ollama_status(OLLAMA_HOST)
    return jsonify(status)


if __name__ == "__main__":
    port = int(os.environ.get("FLASK_PORT", 5001))
    print(f"Doctor Address Verifier starting on port {port}")
    print(f"Ollama: {'disabled' if NO_OLLAMA else f'{OLLAMA_HOST} ({OLLAMA_MODEL})'}")
    print(f"Web crawling: {'enabled' if ENABLE_CRAWLING else 'disabled'}")
    app.run(host="0.0.0.0", port=port, debug=False)
