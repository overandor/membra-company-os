"""
Core verification engine for doctor address verification.

Queries NPPES API, performs real web crawling of provider directories,
generates proof links, and uses Ollama for LLM-based analysis of all evidence.
"""

import re
import time
import json
import urllib.parse
import requests

from web_crawler import crawl_all_sources, summarize_crawl_results


NPPES_API = "https://npiregistry.cms.hhs.gov/api/"

# Known hospital system addresses for automatic recognition
HOSPITAL_SYSTEMS = {
    "111 E 210": {"name": "Montefiore Moses Campus", "tag": "MONTEFIORE-CAMPUS",
                  "url": "https://www.montefiore.org/locations"},
    "3444 KOSSUTH": {"name": "Montefiore Family Care Center", "tag": "MONTEFIORE-FCC",
                     "url": "https://www.monte.org/mmg-family-care-center"},
    "3424 KOSSUTH": {"name": "North Central Bronx Hospital", "tag": "NCB-HOSPITAL",
                     "url": "https://www.nychealthandhospitals.org/northcentralbronx/"},
    "1400 PELHAM": {"name": "Jacobi Medical Center", "tag": "JACOBI-CAMPUS",
                    "url": "https://www.nychealthandhospitals.org/jacobi/"},
    "3415 BAINBRIDGE": {"name": "CHAM / Montefiore", "tag": "MONTEFIORE-CHAM",
                        "url": "https://www.cham.org/"},
    "3400 BAINBRIDGE": {"name": "Montefiore Greene Pavilion", "tag": "MONTEFIORE-CHAM",
                        "url": "https://www.cham.org/"},
    "1621 EASTCHESTER": {"name": "Montefiore Eastchester", "tag": "MONTEFIORE-EASTCHESTER",
                         "url": "https://www.montefiore.org/locations"},
    "600 E 233": {"name": "NCB Hospital", "tag": "NCB-HOSPITAL",
                  "url": "https://www.nychealthandhospitals.org/northcentralbronx/"},
    "1650 GRAND": {"name": "BronxCare Health System", "tag": "BRONXCARE",
                   "url": "https://www.bronxcare.org/"},
    "2015 GRAND": {"name": "BronxCare Health System", "tag": "BRONXCARE",
                   "url": "https://www.bronxcare.org/"},
    "GRACE CHURCH": {"name": "Open Door Family Medical", "tag": "OPEN-DOOR",
                     "url": "https://www.opendoormedical.org/"},
    "N 7TH AVE": {"name": "Montefiore Mount Vernon", "tag": "MONTEFIORE-MV",
                  "url": "https://www.montefiore.org/montefiore-mount-vernon"},
    "1250 WATERS": {"name": "Montefiore at Waters Place", "tag": "MONTEFIORE-WATERS",
                    "url": "https://www.montefiore.org/locations"},
    "1500 WATERS": {"name": "Montefiore at Waters Place", "tag": "MONTEFIORE-WATERS",
                    "url": "https://www.montefiore.org/locations"},
    "1510 WATERS": {"name": "Montefiore at Waters Place", "tag": "MONTEFIORE-WATERS",
                    "url": "https://www.montefiore.org/locations"},
}


def query_nppes(first_name, last_name, state="NY", city=None):
    """Query the NPPES NPI Registry API."""
    first_search = first_name.split()[0] if first_name else ""
    params = {
        "version": "2.1",
        "first_name": first_search,
        "last_name": last_name,
        "state": state,
        "enumeration_type": "NPI-1",
        "limit": 10,
    }
    if city:
        params["city"] = city

    try:
        resp = requests.get(NPPES_API, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("result_count", 0) > 0:
            return data["results"]
    except Exception:
        pass
    return []


def find_best_npi_match(results, last_name, first_name):
    """Find the best matching NPI record from NPPES results."""
    first_upper = first_name.upper().split()[0] if first_name else ""
    last_upper = last_name.upper()

    for r in results:
        basic = r.get("basic", {})
        npi_first = basic.get("first_name", "").upper()
        npi_last = basic.get("last_name", "").upper()

        if last_upper == npi_last and (
            first_upper in npi_first or npi_first.startswith(first_upper)
        ):
            addresses = r.get("addresses", [])
            practice_addr = None
            mailing_addr = None
            practice_full = {}
            mailing_full = {}

            for a in addresses:
                addr_str = (
                    f"{a.get('address_1', '')}, {a.get('city', '')}, "
                    f"{a.get('state', '')} {a.get('postal_code', '')[:5]}"
                )
                if a.get("address_purpose") == "LOCATION":
                    practice_addr = addr_str
                    practice_full = a
                elif a.get("address_purpose") == "MAILING":
                    mailing_addr = addr_str
                    mailing_full = a

            npi_number = r.get("number", "")
            npi_link = (
                f"https://npiregistry.cms.hhs.gov/api/?version=2.1&number={npi_number}"
                if npi_number
                else ""
            )

            return {
                "npi": npi_number,
                "npi_link": npi_link,
                "practice_address": practice_addr or mailing_addr or "",
                "mailing_address": mailing_addr or "",
                "practice_full": practice_full,
                "mailing_full": mailing_full,
                "name": f"{npi_first} {npi_last}",
            }
    return None


def check_address_match(sheet_addr, npi_addr):
    """Fuzzy address comparison."""
    if not sheet_addr or not npi_addr:
        return False

    s = re.sub(r"[#,.\-/]", " ", str(sheet_addr).upper()).split()
    n = re.sub(r"[#,.\-/]", " ", str(npi_addr).upper()).split()

    noise = {"FL", "STE", "APT", "BLDG", "RM", "SUITE", "FLOOR", "UNIT", "BSMT"}
    s_clean = [w for w in s if w not in noise and len(w) > 1]
    n_clean = [w for w in n if w not in noise and len(w) > 1]

    if not s_clean or not n_clean:
        return False

    if s_clean[0] == n_clean[0]:
        s_words = set(s_clean[1:4])
        n_words = set(n_clean[1:4])
        if s_words & n_words:
            return True

    return False


def generate_proof_links(first_name, last_name, address, city, state, zipcode):
    """Generate all verification proof links for a doctor."""
    query = f"{first_name} {last_name} MD {address} {city} {state} {zipcode}"

    links = {
        "google_maps": (
            f"https://www.google.com/maps/search/?api=1"
            f"&query={urllib.parse.quote(query)}"
        ),
        "doximity": (
            f"https://www.google.com/search?q=site%3Adoximity.com%2Fpub+"
            f"%22{urllib.parse.quote(last_name)}%22+"
            f"%22{urllib.parse.quote(first_name)}%22+"
            f"%22{urllib.parse.quote(city)}%22"
        ),
        "webmd": (
            f"https://www.google.com/search?q=site%3Adoctor.webmd.com+"
            f"%22{urllib.parse.quote(last_name)}%22+"
            f"%22{urllib.parse.quote(first_name)}%22+"
            f"%22{urllib.parse.quote(city)}%22"
        ),
        "healthgrades": (
            f"https://www.google.com/search?q=site%3Ahealthgrades.com+"
            f"%22{urllib.parse.quote(last_name)}%22+"
            f"%22{urllib.parse.quote(first_name)}%22+"
            f"%22{urllib.parse.quote(city)}%22"
        ),
        "general": (
            f"https://www.google.com/search?q=%22{urllib.parse.quote(first_name)}+"
            f"{urllib.parse.quote(last_name)}%22+"
            f"%22{urllib.parse.quote(address)}%22+"
            f"%22{urllib.parse.quote(city)}%22+doctor"
        ),
        "montefiore_search": (
            f"https://doctors.montefioreeinstein.org/search?"
            f"query={urllib.parse.quote(first_name + ' ' + last_name)}"
        ),
        "nychh_search": (
            f"https://www.nychealthandhospitals.org/doctors/"
            f"?_doctor_search={urllib.parse.quote(last_name)}"
        ),
    }
    return links


def detect_hospital_system(address):
    """Check if address belongs to a known hospital system."""
    addr_upper = str(address).upper()
    for pattern, info in HOSPITAL_SYSTEMS.items():
        if pattern in addr_upper:
            return info
    return None


def call_ollama(prompt, host="http://localhost:11434", model="llama3.1"):
    """Call Ollama API for LLM analysis."""
    url = f"{host}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 800},
    }
    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        return f"LLM unavailable: {e}"


def check_ollama_status(host="http://localhost:11434"):
    """Check if Ollama is running and responsive."""
    try:
        resp = requests.get(f"{host}/api/tags", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            return {"running": True, "models": models}
    except Exception:
        pass
    return {"running": False, "models": []}


def pull_ollama_model(model="llama3.1", host="http://localhost:11434"):
    """Pull a model in Ollama (blocking)."""
    try:
        resp = requests.post(
            f"{host}/api/pull",
            json={"name": model, "stream": False},
            timeout=600,  # Models can take a while to download
        )
        return resp.status_code == 200
    except Exception:
        return False


def build_llm_prompt(doctor_name, sheet_address, sheet_city, npi_data,
                     hospital_info, crawl_summary=None):
    """
    Build a comprehensive prompt for Ollama to analyze ALL verification evidence.
    Now includes real crawled web data alongside NPPES and hospital detection.
    """
    prompt = f"""You are a healthcare provider address verification agent.
You have access to multiple data sources including the federal NPPES registry,
real-time web crawling of provider directories (Doximity, Healthgrades, WebMD),
and hospital system databases.

Analyze ALL the following evidence and determine if the doctor's address is correct.

DOCTOR: {doctor_name}
SHEET ADDRESS: {sheet_address}, {sheet_city}

=== NPPES REGISTRY DATA ===
"""
    if npi_data:
        prompt += f"""  NPI: {npi_data['npi']}
  Name in NPPES: {npi_data['name']}
  Practice Address: {npi_data['practice_address']}
  Mailing Address: {npi_data['mailing_address']}
"""
    else:
        prompt += "  No NPPES record found.\n"

    if hospital_info:
        prompt += f"""
=== HOSPITAL SYSTEM MATCH ===
  System: {hospital_info['name']}
  Tag: {hospital_info['tag']}
"""

    if crawl_summary:
        prompt += f"""
=== WEB CRAWLING EVIDENCE ===
  Sources checked: {crawl_summary['sources_checked']}
  Sources with confirmed address: {crawl_summary['sources_with_address']}
"""
        if crawl_summary['addresses_found']:
            prompt += "  Addresses found:\n"
            for source, addr in crawl_summary['addresses_found']:
                prompt += f"    - {source}: {addr}\n"
        if crawl_summary['address_consensus']:
            prompt += f"  Consensus address: {crawl_summary['address_consensus']}\n"
        prompt += f"\n  Full evidence:\n{crawl_summary['evidence_summary']}\n"

    prompt += """
=== YOUR TASK ===
Based on ALL the evidence above (NPPES, hospital system, and web crawling),
provide your analysis. Weigh multiple confirming sources more heavily.

1. VERDICT: One of [EXTERNALLY SUPPORTED, REVIEW - <reason>, UNVERIFIED]
2. CONFIDENCE: One of [High, Medium, Low]
3. EXPLANATION: 2-3 sentences summarizing your reasoning across all evidence sources.
4. CORRECTED_ADDRESS: If the address should be different based on evidence, provide it. Otherwise write "N/A".
5. SOURCES_CONFIRMING: Number of independent sources that confirm the address.

Format your response as:
VERDICT: ...
CONFIDENCE: ...
EXPLANATION: ...
CORRECTED_ADDRESS: ...
SOURCES_CONFIRMING: ...
"""
    return prompt


def parse_llm_response(response):
    """Parse structured fields from LLM response."""
    result = {
        "verdict": "REVIEW",
        "confidence": "Medium",
        "explanation": "",
        "corrected_address": "",
        "sources_confirming": 0,
    }

    for line in response.strip().split("\n"):
        line = line.strip()
        if line.startswith("VERDICT:"):
            result["verdict"] = line.replace("VERDICT:", "").strip()
        elif line.startswith("CONFIDENCE:"):
            result["confidence"] = line.replace("CONFIDENCE:", "").strip()
        elif line.startswith("EXPLANATION:"):
            result["explanation"] = line.replace("EXPLANATION:", "").strip()
        elif line.startswith("CORRECTED_ADDRESS:"):
            val = line.replace("CORRECTED_ADDRESS:", "").strip()
            if val.upper() not in ("N/A", "NONE", ""):
                result["corrected_address"] = val
        elif line.startswith("SOURCES_CONFIRMING:"):
            try:
                result["sources_confirming"] = int(
                    line.replace("SOURCES_CONFIRMING:", "").strip()
                )
            except ValueError:
                pass

    return result


def verify_doctor(doctor, ollama_host=None, ollama_model=None,
                  use_ollama=True, enable_crawling=True):
    """
    Verify a single doctor's address using all available methods.

    Args:
        doctor: dict with keys: name, address, city, state, zip, specialty
        ollama_host: Ollama API endpoint
        ollama_model: Model name
        use_ollama: Whether to use LLM analysis
        enable_crawling: Whether to perform real web crawling

    Returns:
        dict with verification results including crawl evidence
    """
    name = doctor["name"]
    parts = name.split(", ")
    last_name = parts[0].strip()
    first_name = parts[1].strip() if len(parts) > 1 else ""

    sheet_addr = str(doctor.get("address", ""))
    sheet_city = str(doctor.get("city", ""))
    sheet_state = str(doctor.get("state", "NY"))
    sheet_zip = str(doctor.get("zip", ""))

    result = {
        "doctor_name": name,
        "visit_readiness": "",
        "confidence": "",
        "verification_method": "",
        "evidence_note": "",
        "nppes_address": "",
        "corrected_address": "",
        "routing_action": "",
        "nppes_link": "",
        "hospital_page_link": "",
        "doximity_link": "",
        "webmd_link": "",
        "healthgrades_link": "",
        "google_maps_link": "",
        "all_evidence_links": "",
        "llm_analysis": "",
        "crawl_sources_checked": 0,
        "crawl_sources_confirmed": 0,
        "crawl_evidence": "",
    }

    methods = []
    evidence_links = []

    # 1. NPPES lookup (with city, then without)
    npi_results = query_nppes(first_name, last_name, city=sheet_city)
    if not npi_results:
        npi_results = query_nppes(first_name, last_name)

    npi_match = find_best_npi_match(npi_results, last_name, first_name)

    if npi_match:
        result["nppes_link"] = npi_match["npi_link"]
        result["nppes_address"] = npi_match["practice_address"]
        evidence_links.append(npi_match["npi_link"])

        if check_address_match(sheet_addr, npi_match["practice_address"]):
            methods.append("NPPES-MATCH")
        elif check_address_match(sheet_addr, npi_match["mailing_address"]):
            methods.append("NPPES-MAILING-MATCH")
        else:
            methods.append("NPPES-MISMATCH")
    else:
        methods.append("NPPES-NOT-FOUND")

    # 2. Hospital system detection
    hospital_info = detect_hospital_system(sheet_addr)
    if hospital_info:
        result["hospital_page_link"] = hospital_info["url"]
        evidence_links.append(hospital_info["url"])
        methods.append(hospital_info["tag"])

    # 3. Generate proof links (always, for manual verification)
    links = generate_proof_links(
        first_name, last_name, sheet_addr, sheet_city, sheet_state, sheet_zip
    )
    result["doximity_link"] = links["doximity"]
    result["webmd_link"] = links["webmd"]
    result["healthgrades_link"] = links["healthgrades"]
    result["google_maps_link"] = links["google_maps"]
    evidence_links.extend(
        [
            links["google_maps"],
            links["doximity"],
            links["webmd"],
            links["healthgrades"],
            links["montefiore_search"],
            links["nychh_search"],
        ]
    )

    # 4. REAL WEB CRAWLING — scrape actual pages for address data
    crawl_summary = None
    if enable_crawling:
        try:
            crawl_results = crawl_all_sources(
                first_name=first_name,
                last_name=last_name,
                address=sheet_addr,
                city=sheet_city,
                state=sheet_state,
                npi_number=npi_match["npi"] if npi_match else "",
                is_hospital_system=hospital_info is not None,
            )
            crawl_summary = summarize_crawl_results(crawl_results)
            result["crawl_sources_checked"] = crawl_summary["sources_checked"]
            result["crawl_sources_confirmed"] = crawl_summary["sources_with_address"]
            result["crawl_evidence"] = crawl_summary["evidence_summary"]

            # Add crawl URLs to evidence links
            evidence_links.extend(crawl_summary["all_urls"])

            if crawl_summary["sources_with_address"] > 0:
                methods.append(f"WEB-CRAWL-{crawl_summary['sources_with_address']}-SOURCES")
        except Exception as e:
            result["crawl_evidence"] = f"Crawling failed: {str(e)}"

    result["verification_method"] = " | ".join(methods)
    result["all_evidence_links"] = " ; ".join(
        [link for link in evidence_links if link]
    )

    # 5. Rule-based verdict (baseline before LLM)
    if "NPPES-MATCH" in methods:
        result["visit_readiness"] = "EXTERNALLY SUPPORTED"
        result["confidence"] = "High"
        result["evidence_note"] = (
            f"NPPES confirms address. NPI: {npi_match['npi']}. "
            f"Practice location: {npi_match['practice_address']}"
        )
        result["routing_action"] = "Keep"
    elif "NPPES-MAILING-MATCH" in methods:
        result["visit_readiness"] = "EXTERNALLY SUPPORTED"
        result["confidence"] = "Medium"
        result["evidence_note"] = (
            f"NPPES mailing address matches. NPI: {npi_match['npi']}. "
            f"Practice location differs: {npi_match['practice_address']}"
        )
        result["routing_action"] = "Keep - confirm practice vs mailing"
    elif "NPPES-MISMATCH" in methods:
        result["visit_readiness"] = "REVIEW - address mismatch"
        result["confidence"] = "Medium"
        result["evidence_note"] = (
            f"NPPES NPI {npi_match['npi']} shows different address: "
            f"{npi_match['practice_address']}"
        )
        result["corrected_address"] = npi_match["practice_address"]
        result["routing_action"] = "Verify before routing"
    else:
        result["visit_readiness"] = "REVIEW - no NPPES record"
        result["confidence"] = "Low"
        result["evidence_note"] = "No NPPES record found. Phone-confirm before routing."
        result["routing_action"] = "Phone-confirm required"

    # 6. Upgrade confidence if hospital system matches
    if hospital_info and "NPPES-MATCH" in methods:
        result["confidence"] = "High"
        result["evidence_note"] += f" Confirmed {hospital_info['name']} location."

    # 7. Upgrade confidence if multiple web sources confirm
    if crawl_summary and crawl_summary["sources_with_address"] >= 2:
        if result["confidence"] == "Low":
            result["confidence"] = "Medium"
        result["evidence_note"] += (
            f" {crawl_summary['sources_with_address']} web sources confirm address."
        )

    # 8. Ollama LLM analysis — feed ALL evidence for comprehensive analysis
    if use_ollama and ollama_host:
        prompt = build_llm_prompt(
            name, sheet_addr, sheet_city, npi_match, hospital_info, crawl_summary
        )
        llm_response = call_ollama(prompt, host=ollama_host, model=ollama_model)
        result["llm_analysis"] = llm_response

        if "LLM unavailable" not in llm_response:
            parsed = parse_llm_response(llm_response)
            # LLM verdict overrides rule-based when LLM has more evidence
            if parsed["verdict"]:
                result["visit_readiness"] = parsed["verdict"]
            if parsed["confidence"]:
                result["confidence"] = parsed["confidence"]
            if parsed["explanation"]:
                result["evidence_note"] += f" LLM: {parsed['explanation']}"
            if parsed["corrected_address"]:
                result["corrected_address"] = parsed["corrected_address"]

    return result
