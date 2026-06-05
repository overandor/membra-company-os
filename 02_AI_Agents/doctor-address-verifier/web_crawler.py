"""
Real web crawling module for doctor address verification.

Scrapes actual provider directory pages to extract confirmed addresses:
  - Doximity provider profiles
  - Healthgrades physician pages
  - WebMD doctor listings
  - Hospital provider directories (Montefiore Einstein, NYC H+H)
  - Google Maps address lookups
  - NPI lookup aggregator sites

Each crawler returns a dict with:
  - source: str — name of the source
  - url: str — URL that was fetched
  - address_found: str — extracted address (empty if none found)
  - raw_snippet: str — relevant text snippet from the page
  - success: bool — whether the crawl succeeded
  - error: str — error message if failed
"""

import re
import time
import urllib.parse
from typing import Optional

import requests
from bs4 import BeautifulSoup

# Common headers to appear as a regular browser
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Rate-limit delay between requests to same domain (seconds)
CRAWL_DELAY = 0.5
TIMEOUT = 12


def _safe_get(url: str, timeout: int = TIMEOUT) -> Optional[requests.Response]:
    """Fetch a URL safely with error handling."""
    try:
        resp = requests.get(
            url, headers=HEADERS,
            timeout=timeout, allow_redirects=True,
        )
        if resp.status_code == 200:
            return resp
    except Exception:
        pass
    return None


def _extract_text(soup: BeautifulSoup) -> str:
    """Extract visible text from parsed HTML."""
    for tag in soup(["script", "style", "noscript", "meta", "link"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def _find_address_in_text(
    text: str, city_hint: str = "",
    state_hint: str = "NY",
) -> str:
    """
    Try to extract a US street address from a text block.
    Looks for patterns like: 123 Main St, City, ST 12345
    """
    # Pattern: number + street name + optional city/state/zip
    addr_pattern = re.compile(
        r'\b(\d{1,5}\s+[A-Za-z0-9.\-\s]{3,40}'
        r'(?:St(?:reet)?|Ave(?:nue)?|Blvd|Boulevard|Dr(?:ive)?|Rd|Road|'
        r'Ln|Lane|Way|Pl(?:ace)?|Pkwy|Parkway|Ct|Court|Ter(?:race)?|'
        r'Cir(?:cle)?|Hwy|Highway)'
        r'[.,]?\s*(?:[A-Za-z\s]{2,25}[.,]?\s*)?'
        r'(?:NY|NJ|CT|PA|New York|New Jersey|Connecticut|Pennsylvania)?'
        r'\s*\d{5}(?:-\d{4})?)\b',
        re.IGNORECASE,
    )
    matches = addr_pattern.findall(text)

    if city_hint and matches:
        city_upper = city_hint.upper()
        for m in matches:
            if city_upper in m.upper():
                return m.strip()

    if matches:
        return matches[0].strip()
    return ""


def _find_address_near_keyword(
    text: str, keywords: list, window: int = 300,
) -> str:
    """Search for address patterns near specific keywords in text."""
    text_lower = text.lower()
    for kw in keywords:
        idx = text_lower.find(kw.lower())
        if idx >= 0:
            start = max(0, idx - 50)
            end = min(len(text), idx + window)
            snippet = text[start:end]
            addr = _find_address_in_text(snippet)
            if addr:
                return addr
    return ""


# ── Individual Crawlers ──────────────────────────────────────────────


def crawl_npi_profile(npi_number: str) -> dict:
    """
    Crawl npiprofile.com for additional address data beyond the API.
    This site renders server-side and contains practice locations.
    """
    result = {
        "source": "NPI Profile",
        "url": "",
        "address_found": "",
        "raw_snippet": "",
        "success": False,
        "error": "",
    }

    if not npi_number:
        result["error"] = "No NPI number provided"
        return result

    url = f"https://npiprofile.com/npi/{npi_number}"
    result["url"] = url

    resp = _safe_get(url)
    if not resp:
        result["error"] = "Failed to fetch page"
        return result

    soup = BeautifulSoup(resp.text, "lxml")
    text = _extract_text(soup)

    # Look for address near keywords
    addr = _find_address_near_keyword(
        text,
        ["Practice Location", "Mailing Address",
         "Office Address", "Location"],
    )
    if addr:
        result["address_found"] = addr
        result["raw_snippet"] = addr
        result["success"] = True
    else:
        # Try the whole page
        addr = _find_address_in_text(text)
        if addr:
            result["address_found"] = addr
            result["raw_snippet"] = addr
            result["success"] = True
        else:
            result["error"] = "No address found on page"

    return result


def crawl_doximity(first_name: str, last_name: str, city: str = "") -> dict:
    """
    Search Doximity for a provider profile and extract their practice address.
    Doximity profiles are at: doximity.com/pub/firstname-lastname-md
    """
    result = {
        "source": "Doximity",
        "url": "",
        "address_found": "",
        "raw_snippet": "",
        "success": False,
        "error": "",
    }

    # Construct likely profile URL
    first_clean = re.sub(r"[^a-z]", "", first_name.lower().split()[0])
    last_clean = re.sub(r"[^a-z]", "", last_name.lower())
    profile_url = f"https://www.doximity.com/pub/{first_clean}-{last_clean}-md"
    result["url"] = profile_url

    resp = _safe_get(profile_url)
    if not resp:
        # Try without -md suffix
        dox = "https://www.doximity.com/pub"
        profile_url = f"{dox}/{first_clean}-{last_clean}"
        resp = _safe_get(profile_url)
        if not resp:
            result["error"] = "Profile page not reachable"
            return result
        result["url"] = profile_url

    soup = BeautifulSoup(resp.text, "lxml")
    text = _extract_text(soup)

    # Doximity puts addresses near "Office" or "Practice" keywords
    addr = _find_address_near_keyword(
        text,
        ["Office", "Practice Location",
         "Practice Address", "Hospital Affiliation"],
    )
    if not addr:
        addr = _find_address_in_text(text, city_hint=city)
    if addr:
        result["address_found"] = addr
        result["raw_snippet"] = addr[:200]
        result["success"] = True
    else:
        result["error"] = "No address extracted from profile"

    time.sleep(CRAWL_DELAY)
    return result


def crawl_healthgrades(
    first_name: str, last_name: str,
    city: str = "", state: str = "NY",
) -> dict:
    """
    Search Healthgrades for provider and extract practice address.
    Uses their search endpoint to find the provider page.
    """
    result = {
        "source": "Healthgrades",
        "url": "",
        "address_found": "",
        "raw_snippet": "",
        "success": False,
        "error": "",
    }

    first_clean = first_name.split()[0].lower()
    last_clean = last_name.lower().replace(" ", "-")
    hg = "https://www.healthgrades.com/usearch"
    slug = f"dr-{first_clean}-{last_clean}"
    if city:
        where = f"{city.lower()}%2C+{state.lower()}"
        search_url = (
            f"{hg}?what={slug}&where={where}"
        )
    else:
        search_url = f"{hg}?what={slug}"
    result["url"] = search_url

    resp = _safe_get(search_url)
    if not resp:
        result["error"] = "Search page not reachable"
        return result

    soup = BeautifulSoup(resp.text, "lxml")
    text = _extract_text(soup)

    # Look for practice address in results
    addr = _find_address_near_keyword(
        text, ["Practice", "Office", "Location", last_name.title()],
    )
    if not addr:
        addr = _find_address_in_text(text, city_hint=city)
    if addr:
        result["address_found"] = addr
        result["raw_snippet"] = addr[:200]
        result["success"] = True
    else:
        # Try direct physician URL pattern
        slug = f"dr-{first_clean}-{last_clean}"
        direct_url = f"https://www.healthgrades.com/physician/{slug}"
        resp2 = _safe_get(direct_url)
        if resp2:
            result["url"] = direct_url
            soup2 = BeautifulSoup(resp2.text, "lxml")
            text2 = _extract_text(soup2)
            addr = _find_address_in_text(text2, city_hint=city)
            if addr:
                result["address_found"] = addr
                result["raw_snippet"] = addr[:200]
                result["success"] = True
            else:
                result["error"] = "No address on physician page"
        else:
            result["error"] = "No address found in search results"

    time.sleep(CRAWL_DELAY)
    return result


def crawl_webmd(
    first_name: str, last_name: str,
    city: str = "", state: str = "NY",
) -> dict:
    """
    Search WebMD doctor directory for provider address.
    """
    result = {
        "source": "WebMD",
        "url": "",
        "address_found": "",
        "raw_snippet": "",
        "success": False,
        "error": "",
    }

    first_clean = first_name.split()[0].lower()
    last_clean = last_name.lower()
    search_url = (
        f"https://doctor.webmd.com/find-a-doctor/results?"
        f"name={urllib.parse.quote(first_clean + ' ' + last_clean)}"
        f"&city={urllib.parse.quote(city)}&state={state}"
    )
    result["url"] = search_url

    resp = _safe_get(search_url)
    if not resp:
        result["error"] = "Search page not reachable"
        return result

    soup = BeautifulSoup(resp.text, "lxml")
    text = _extract_text(soup)

    addr = _find_address_near_keyword(
        text, ["Address", "Office", "Location", last_name.title()]
    )
    if not addr:
        addr = _find_address_in_text(text, city_hint=city)
    if addr:
        result["address_found"] = addr
        result["raw_snippet"] = addr[:200]
        result["success"] = True
    else:
        result["error"] = "No address found in search results"

    time.sleep(CRAWL_DELAY)
    return result


def crawl_montefiore(first_name: str, last_name: str) -> dict:
    """
    Search the Montefiore Einstein doctor finder for provider address.
    """
    result = {
        "source": "Montefiore Einstein",
        "url": "",
        "address_found": "",
        "raw_snippet": "",
        "success": False,
        "error": "",
    }

    search_url = (
        f"https://doctors.montefioreeinstein.org/search?"
        f"query={urllib.parse.quote(first_name + ' ' + last_name)}"
    )
    result["url"] = search_url

    resp = _safe_get(search_url)
    if not resp:
        result["error"] = "Search page not reachable"
        return result

    soup = BeautifulSoup(resp.text, "lxml")
    text = _extract_text(soup)

    addr = _find_address_near_keyword(
        text, ["Location", "Office", "Address", last_name.title()]
    )
    if not addr:
        addr = _find_address_in_text(text, city_hint="BRONX")
    if addr:
        result["address_found"] = addr
        result["raw_snippet"] = addr[:200]
        result["success"] = True
    else:
        result["error"] = "No address found in search"

    time.sleep(CRAWL_DELAY)
    return result


def crawl_nychh(first_name: str, last_name: str) -> dict:
    """
    Search NYC Health + Hospitals doctor directory.
    """
    result = {
        "source": "NYC Health + Hospitals",
        "url": "",
        "address_found": "",
        "raw_snippet": "",
        "success": False,
        "error": "",
    }

    search_url = (
        f"https://www.nychealthandhospitals.org/doctors/"
        f"?_doctor_search={urllib.parse.quote(last_name)}"
    )
    result["url"] = search_url

    resp = _safe_get(search_url)
    if not resp:
        result["error"] = "Search page not reachable"
        return result

    soup = BeautifulSoup(resp.text, "lxml")
    text = _extract_text(soup)

    # Look for address near the doctor's name
    full_name = f"{first_name} {last_name}".title()
    addr = _find_address_near_keyword(
        text, [full_name, last_name.title(), "Location", "Address"]
    )
    if not addr:
        addr = _find_address_in_text(text, city_hint="BRONX")
    if addr:
        result["address_found"] = addr
        result["raw_snippet"] = addr[:200]
        result["success"] = True
    else:
        result["error"] = "No address found in search"

    time.sleep(CRAWL_DELAY)
    return result


def crawl_google_verification(
    first_name: str, last_name: str,
    address: str, city: str, state: str = "NY"
) -> dict:
    """
    Use DuckDuckGo (less restrictive than Google) to search for the doctor
    and extract address-related snippets.
    """
    result = {
        "source": "Web Search (DuckDuckGo)",
        "url": "",
        "address_found": "",
        "raw_snippet": "",
        "success": False,
        "error": "",
    }

    query = (
        f'"{first_name} {last_name}" doctor'
        f' "{city}" "{address}"'
    )
    ddg = "https://html.duckduckgo.com/html/"
    search_url = f"{ddg}?q={urllib.parse.quote(query)}"
    result["url"] = search_url

    resp = _safe_get(search_url, timeout=15)
    if not resp:
        result["error"] = "Search not reachable"
        return result

    soup = BeautifulSoup(resp.text, "lxml")

    # Extract search result snippets
    snippets = []
    for res in soup.select(".result__snippet"):
        snippets.append(res.get_text(strip=True))
    for res in soup.select(".result__body"):
        snippets.append(res.get_text(strip=True))

    combined = " ".join(snippets[:5])
    if combined:
        result["raw_snippet"] = combined[:400]
        # Check if the address appears in search results
        addr_parts = address.upper().split()[:3]
        valid = [p for p in addr_parts if len(p) > 2]
        if any(p in combined.upper() for p in valid):
            result["address_found"] = address
            result["success"] = True
        else:
            addr = _find_address_in_text(combined, city_hint=city)
            if addr:
                result["address_found"] = addr
                result["success"] = True
            else:
                result["error"] = "Address not confirmed in search results"
    else:
        result["error"] = "No search results found"

    time.sleep(CRAWL_DELAY)
    return result


# ── Main Crawl Orchestrator ──────────────────────────────────────────


def crawl_all_sources(
    first_name: str,
    last_name: str,
    address: str,
    city: str,
    state: str = "NY",
    npi_number: str = "",
    is_hospital_system: bool = False,
) -> list:
    """
    Run all crawlers for a single doctor and collect results.

    Returns a list of crawler result dicts.
    """
    results = []

    # 1. NPI Profile (additional data beyond the API)
    if npi_number:
        results.append(crawl_npi_profile(npi_number))

    # 2. Doximity
    results.append(crawl_doximity(first_name, last_name, city))

    # 3. Healthgrades
    results.append(crawl_healthgrades(first_name, last_name, city, state))

    # 4. WebMD
    results.append(crawl_webmd(first_name, last_name, city, state))

    # 5. Hospital-specific directories
    if is_hospital_system:
        results.append(crawl_montefiore(first_name, last_name))
        results.append(crawl_nychh(first_name, last_name))

    # 6. Web search verification
    results.append(
        crawl_google_verification(first_name, last_name, address, city, state)
    )

    return results


def summarize_crawl_results(crawl_results: list) -> dict:
    """
    Summarize crawl results into a structured summary for LLM analysis.

    Returns dict with:
      - sources_checked: int
      - sources_with_address: int
      - addresses_found: list of (source, address) tuples
      - address_consensus: str — most commonly found address (if any)
      - evidence_summary: str — human-readable summary
      - all_urls: list of URLs checked
    """
    sources_checked = len(crawl_results)
    addresses = []
    urls = []

    for r in crawl_results:
        urls.append(r["url"])
        if r["success"] and r["address_found"]:
            addresses.append((r["source"], r["address_found"]))

    # Find consensus address (simple: most common)
    consensus = ""
    if addresses:
        # Normalize addresses for comparison
        addr_counts = {}
        for source, addr in addresses:
            key = re.sub(r"[^A-Z0-9]", "", addr.upper())[:30]
            if key not in addr_counts:
                addr_counts[key] = {"count": 0, "full": addr, "sources": []}
            addr_counts[key]["count"] += 1
            addr_counts[key]["sources"].append(source)

        best = max(addr_counts.values(), key=lambda x: x["count"])
        consensus = best["full"]

    # Build summary
    summary_parts = [f"Checked {sources_checked} web sources."]
    if addresses:
        summary_parts.append(f"Found addresses from {len(addresses)} sources:")
        for source, addr in addresses:
            summary_parts.append(f"  - {source}: {addr}")
    else:
        summary_parts.append("No addresses extracted from any web source.")

    return {
        "sources_checked": sources_checked,
        "sources_with_address": len(addresses),
        "addresses_found": addresses,
        "address_consensus": consensus,
        "evidence_summary": "\n".join(summary_parts),
        "all_urls": [u for u in urls if u],
    }
