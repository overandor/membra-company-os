"""
Hugging Face Spaces Gradio app for Doctor Address Verifier.

Provides a web UI to verify healthcare provider addresses using
the NPPES API, real web crawling, and rule-based analysis.
Deployed as a Hugging Face Space for public access.
"""

import os
import sys
import tempfile

# Ensure local modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gradio as gr  # noqa: E402
import pandas as pd  # noqa: E402

from verifier import verify_doctor  # noqa: E402


def verify_single(
    name: str, address: str, city: str,
    state: str, zipcode: str, specialty: str,
) -> dict:
    """Verify a single doctor's address."""
    doctor = {
        "name": name.strip(),
        "address": address.strip(),
        "city": city.strip(),
        "state": state.strip() or "NY",
        "zip": zipcode.strip(),
        "specialty": specialty.strip(),
    }
    if not doctor["name"]:
        return {"error": "Doctor name is required."}

    result = verify_doctor(
        doctor,
        use_ollama=False,
        enable_crawling=True,
    )
    return result


def format_single_result(result: dict) -> str:
    """Format verification result as markdown."""
    if "error" in result:
        return f"**Error:** {result['error']}"

    vr = result.get("visit_readiness", "Unknown")
    conf = result.get("confidence", "Unknown")
    method = result.get("verification_method", "")
    note = result.get("evidence_note", "")
    nppes = result.get("nppes_address", "")
    corrected = result.get("corrected_address", "")
    crawl_checked = result.get("crawl_sources_checked", 0)
    crawl_confirmed = result.get(
        "crawl_sources_confirmed", 0
    )

    md = "## Verification Result\n\n"
    md += f"**Verdict:** {vr}\n\n"
    md += f"**Confidence:** {conf}\n\n"
    md += f"**Method:** {method}\n\n"

    if nppes:
        md += f"**NPPES Address:** {nppes}\n\n"
    if corrected:
        md += f"**Corrected Address:** {corrected}\n\n"

    md += f"**Evidence:** {note}\n\n"

    if crawl_checked > 0:
        md += (
            f"**Web Crawling:** {crawl_confirmed}/"
            f"{crawl_checked} sources confirmed\n\n"
        )

    # Links
    links = []
    for key, label in [
        ("nppes_link", "NPPES Registry"),
        ("hospital_page_link", "Hospital Page"),
        ("doximity_link", "Doximity Search"),
        ("webmd_link", "WebMD Search"),
        ("healthgrades_link", "Healthgrades"),
        ("google_maps_link", "Google Maps"),
    ]:
        url = result.get(key, "")
        if url:
            links.append(f"[{label}]({url})")

    if links:
        md += "**Evidence Links:** "
        md += " | ".join(links)
        md += "\n"

    return md


def verify_single_ui(
    name, address, city, state, zipcode, specialty,
):
    """Gradio handler for single doctor verification."""
    result = verify_single(
        name, address, city, state, zipcode, specialty,
    )
    return format_single_result(result)


def verify_batch_ui(file):
    """Verify a batch of doctors from uploaded Excel."""
    if file is None:
        return "No file uploaded.", None

    try:
        df = pd.read_excel(file.name)
    except Exception as e:
        return f"Error reading file: {e}", None

    # Detect column mapping
    col_map = {}
    for c in df.columns:
        cl = c.lower().strip()
        if (
            "doctor" in cl
            or cl == "name"
            or cl == "provider name"
        ):
            col_map["name"] = c
        elif cl in (
            "address", "street",
            "address_1", "street address",
        ):
            col_map["address"] = c
        elif cl == "city":
            col_map["city"] = c
        elif cl == "state":
            col_map["state"] = c
        elif cl in (
            "zip", "zipcode",
            "zip code", "postal code",
        ):
            col_map["zip"] = c

    if "name" not in col_map:
        return (
            "Could not find a 'Doctor Name' or 'Name' "
            f"column. Found: {list(df.columns)}"
        ), None

    # Add result columns
    new_cols = [
        "Visit Readiness", "Confidence",
        "Verification_Method",
        "External Evidence Note",
        "NPPES_Address", "Corrected Address",
        "Routing Action",
        "NPPES_Link", "Doximity_Link",
        "WebMD_Link", "Healthgrades_Link",
        "Google_Maps_Link",
        "Crawl_Sources_Checked",
        "Crawl_Sources_Confirmed",
    ]
    for col in new_cols:
        if col not in df.columns:
            df[col] = ""

    total = len(df)
    supported = 0
    review = 0

    for idx, row in df.iterrows():
        doctor = {
            "name": str(
                row.get(col_map.get("name", ""), "")
            ),
            "address": str(
                row.get(col_map.get("address", ""), "")
            ),
            "city": str(
                row.get(col_map.get("city", ""), "")
            ),
            "state": str(
                row.get(col_map.get("state", ""), "NY")
            ),
            "zip": str(
                row.get(col_map.get("zip", ""), "")
            ),
        }

        if (
            not doctor["name"]
            or doctor["name"] == "nan"
        ):
            continue

        result = verify_doctor(
            doctor,
            use_ollama=False,
            enable_crawling=True,
        )

        vr = result["visit_readiness"]
        df.at[idx, "Visit Readiness"] = vr
        df.at[idx, "Confidence"] = (
            result["confidence"]
        )
        df.at[idx, "Verification_Method"] = (
            result["verification_method"]
        )
        df.at[idx, "External Evidence Note"] = (
            result["evidence_note"]
        )
        df.at[idx, "NPPES_Address"] = (
            result["nppes_address"]
        )
        df.at[idx, "Corrected Address"] = (
            result["corrected_address"]
        )
        df.at[idx, "Routing Action"] = (
            result["routing_action"]
        )
        df.at[idx, "NPPES_Link"] = (
            result["nppes_link"]
        )
        df.at[idx, "Doximity_Link"] = (
            result["doximity_link"]
        )
        df.at[idx, "WebMD_Link"] = (
            result["webmd_link"]
        )
        df.at[idx, "Healthgrades_Link"] = (
            result["healthgrades_link"]
        )
        df.at[idx, "Google_Maps_Link"] = (
            result["google_maps_link"]
        )
        df.at[idx, "Crawl_Sources_Checked"] = (
            result.get("crawl_sources_checked", 0)
        )
        df.at[idx, "Crawl_Sources_Confirmed"] = (
            result.get("crawl_sources_confirmed", 0)
        )

        if "SUPPORTED" in vr:
            supported += 1
        elif "REVIEW" in vr:
            review += 1

    # Save to temp file
    out_path = os.path.join(
        tempfile.gettempdir(),
        "verified_results.xlsx",
    )
    df.to_excel(out_path, index=False)

    summary = (
        f"## Batch Verification Complete\n\n"
        f"**Total:** {total} doctors\n\n"
        f"**Externally Supported:** {supported}\n\n"
        f"**Needs Review:** {review}\n\n"
        f"Download the verified spreadsheet below."
    )
    return summary, out_path


# ── Build Gradio App ─────────────────────────────────────

with gr.Blocks(
    title="Doctor Address Verifier",
    theme=gr.themes.Soft(),
) as demo:
    gr.Markdown(
        "# Doctor Address Verifier\n\n"
        "Verify healthcare provider addresses using "
        "the **NPPES registry**, **real web crawling** "
        "(Doximity, Healthgrades, WebMD, hospital "
        "directories), and rule-based analysis.\n\n"
        "Upload a spreadsheet for batch verification "
        "or verify a single doctor below."
    )

    with gr.Tab("Single Doctor"):
        with gr.Row():
            with gr.Column():
                name_input = gr.Textbox(
                    label="Doctor Name",
                    placeholder="LASTNAME, FIRSTNAME",
                )
                addr_input = gr.Textbox(
                    label="Address",
                    placeholder="123 Main St",
                )
                city_input = gr.Textbox(
                    label="City",
                    placeholder="Bronx",
                )
                state_input = gr.Textbox(
                    label="State",
                    value="NY",
                )
                zip_input = gr.Textbox(
                    label="ZIP Code",
                    placeholder="10467",
                )
                spec_input = gr.Textbox(
                    label="Specialty (optional)",
                    placeholder="Internal Medicine",
                )
                verify_btn = gr.Button(
                    "Verify Address",
                    variant="primary",
                )
            with gr.Column():
                result_output = gr.Markdown(
                    label="Result",
                )

        verify_btn.click(
            fn=verify_single_ui,
            inputs=[
                name_input, addr_input,
                city_input, state_input,
                zip_input, spec_input,
            ],
            outputs=result_output,
        )

    with gr.Tab("Batch Upload"):
        gr.Markdown(
            "Upload an Excel file (.xlsx) with columns "
            "for Doctor Name, Address, City, State, ZIP."
        )
        file_input = gr.File(
            label="Upload Excel File",
            file_types=[".xlsx", ".xls"],
        )
        batch_btn = gr.Button(
            "Verify All",
            variant="primary",
        )
        batch_output = gr.Markdown(
            label="Results",
        )
        download_output = gr.File(
            label="Download Verified Spreadsheet",
        )

        batch_btn.click(
            fn=verify_batch_ui,
            inputs=file_input,
            outputs=[batch_output, download_output],
        )

    with gr.Tab("About"):
        gr.Markdown(
            "## How It Works\n\n"
            "1. **NPPES Registry** — Queries the CMS "
            "National Plan & Provider Enumeration "
            "System for NPI records\n"
            "2. **Hospital System Detection** — "
            "Recognizes known hospital campuses "
            "(Montefiore, Jacobi, BronxCare, etc.)\n"
            "3. **Web Crawling** — Scrapes Doximity, "
            "Healthgrades, WebMD, and hospital "
            "directories for address confirmation\n"
            "4. **Evidence Links** — Generates "
            "clickable proof links for manual "
            "verification\n\n"
            "### Confidence Levels\n\n"
            "- **High** — Multiple sources confirm "
            "the address\n"
            "- **Medium** — Partial confirmation or "
            "minor discrepancies\n"
            "- **Low** — No external confirmation "
            "found\n\n"
            "### Source Code\n\n"
            "[GitHub Repository]"
            "(https://github.com/overandor/"
            "membra-company-os/tree/main/"
            "02_AI_Agents/doctor-address-verifier)"
        )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
    )
