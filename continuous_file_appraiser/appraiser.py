#!/usr/bin/env python3
"""
Continuous File Appraiser — Ollama-powered dollar valuation of agent work.
Watches a directory tree, appraises each file via local LLM, tracks changes
over time, and emits billable line items.

Usage:
    python appraiser.py [--dir /path] [--model llama3] [--interval 300] [--invoice]
"""

import os
import sys
import json
import time
import hashlib
import argparse
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


LEDGER_FILE = "appraisal_ledger.json"
INVOICE_DIR = "invoices"

SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".tox", ".mypy_cache", ".pytest_cache", "dist", "build",
}
SKIP_EXTENSIONS = {
    ".pyc", ".o", ".so", ".dylib", ".class", ".exe",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".mp3", ".mp4", ".wav", ".m4a", ".mov",
    ".zip", ".tar", ".gz", ".dmg", ".iso",
    ".db", ".sqlite", ".sqlite3",
}

RATE_TABLE = {
    "infrastructure": 185.0,
    "smart_contract": 250.0,
    "trading_system": 225.0,
    "ml_pipeline": 200.0,
    "api_service": 175.0,
    "frontend": 150.0,
    "documentation": 95.0,
    "configuration": 110.0,
    "test": 130.0,
    "script": 120.0,
    "data": 80.0,
    "unknown": 100.0,
}


@dataclass
class FileAppraisal:
    path: str
    sha256: str
    category: str
    complexity_score: float  # 0-1
    dollar_value: float
    hourly_rate: float
    estimated_hours: float
    reasoning: str
    appraised_at: str
    model_used: str
    line_count: int
    size_bytes: int
    previous_value: Optional[float] = None
    delta: float = 0.0

    def to_dict(self):
        return asdict(self)


class OllamaAppraiser:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    async def is_available(self) -> bool:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as r:
                    return r.status == 200
        except Exception:
            return False

    async def appraise(self, model: str, filepath: str, content: str, metadata: dict) -> dict:
        prompt = self._build_prompt(filepath, content, metadata)
        system = (
            "You are a senior software IP appraiser. Given a file, estimate its "
            "dollar value based on: complexity, originality, domain expertise "
            "required, integration effort, and replacement cost. Respond ONLY "
            "with valid JSON: {\"category\": str, \"complexity_score\": float 0-1, "
            "\"estimated_hours\": float, \"reasoning\": str (1-2 sentences)}. "
            "No markdown, no extra text."
        )
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 300},
        }
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as r:
                result = await r.json()
                raw = result.get("response", "{}")
                return self._parse_response(raw)

    def _build_prompt(self, filepath: str, content: str, metadata: dict) -> str:
        snippet = content[:3000] if len(content) > 3000 else content
        return (
            f"File: {filepath}\n"
            f"Lines: {metadata['lines']}, Size: {metadata['size']} bytes\n"
            f"Extension: {metadata['ext']}\n\n"
            f"--- content preview ---\n{snippet}\n--- end ---\n\n"
            f"Appraise this file. What category does it belong to? "
            f"How complex is it (0-1)? How many hours of skilled work does it represent?"
        )

    def _parse_response(self, raw: str) -> dict:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
        try:
            d = json.loads(raw)
            return {
                "category": str(d.get("category", "unknown")).lower().replace(" ", "_"),
                "complexity_score": min(1.0, max(0.0, float(d.get("complexity_score", 0.5)))),
                "estimated_hours": max(0.1, float(d.get("estimated_hours", 1.0))),
                "reasoning": str(d.get("reasoning", "No reasoning provided")),
            }
        except (json.JSONDecodeError, ValueError):
            return {
                "category": "unknown",
                "complexity_score": 0.5,
                "estimated_hours": 1.0,
                "reasoning": f"LLM response could not be parsed: {raw[:200]}",
            }


class ContinuousAppraiser:
    def __init__(self, target_dir: str, model: str = "llama3"):
        self.target_dir = Path(target_dir).resolve()
        self.model = model
        self.ledger_path = self.target_dir / LEDGER_FILE
        self.invoice_dir = self.target_dir / INVOICE_DIR
        self.invoice_dir.mkdir(exist_ok=True)
        self.ollama = OllamaAppraiser()
        self.ledger: Dict[str, dict] = self._load_ledger()

    def _load_ledger(self) -> dict:
        if self.ledger_path.exists():
            with open(self.ledger_path) as f:
                return json.load(f)
        return {}

    def _save_ledger(self):
        with open(self.ledger_path, "w") as f:
            json.dump(self.ledger, f, indent=2)

    def discover_files(self) -> List[Path]:
        files = []
        for root, dirs, filenames in os.walk(self.target_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in filenames:
                p = Path(root) / fname
                if p.suffix.lower() in SKIP_EXTENSIONS:
                    continue
                if fname.startswith("."):
                    continue
                if fname == LEDGER_FILE:
                    continue
                files.append(p)
        return sorted(files)

    def file_hash(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def needs_reappraisal(self, path: Path) -> bool:
        rel = str(path.relative_to(self.target_dir))
        if rel not in self.ledger:
            return True
        return self.ledger[rel].get("sha256") != self.file_hash(path)

    async def appraise_file(self, path: Path) -> FileAppraisal:
        rel = str(path.relative_to(self.target_dir))
        sha = self.file_hash(path)
        stat = path.stat()

        try:
            content = path.read_text(errors="replace")
        except Exception:
            content = ""

        lines = content.count("\n") + (1 if content else 0)
        meta = {"lines": lines, "size": stat.st_size, "ext": path.suffix}

        result = await self.ollama.appraise(self.model, rel, content, meta)

        category = result["category"]
        rate = RATE_TABLE.get(category, RATE_TABLE["unknown"])
        hours = result["estimated_hours"]
        value = round(rate * hours * result["complexity_score"], 2)

        prev = self.ledger.get(rel, {}).get("dollar_value")

        appraisal = FileAppraisal(
            path=rel,
            sha256=sha,
            category=category,
            complexity_score=result["complexity_score"],
            dollar_value=value,
            hourly_rate=rate,
            estimated_hours=hours,
            reasoning=result["reasoning"],
            appraised_at=datetime.now(timezone.utc).isoformat(),
            model_used=self.model,
            line_count=lines,
            size_bytes=stat.st_size,
            previous_value=prev,
            delta=round(value - prev, 2) if prev is not None else 0.0,
        )
        self.ledger[rel] = appraisal.to_dict()
        return appraisal

    async def run_full_appraisal(self) -> List[FileAppraisal]:
        if not await self.ollama.is_available():
            print("ERROR: Ollama is not running at", self.ollama.base_url)
            print("Start it with: ollama serve")
            sys.exit(1)

        files = self.discover_files()
        pending = [f for f in files if self.needs_reappraisal(f)]
        total = len(files)
        to_do = len(pending)

        print(f"\n{'='*60}")
        print(f"  CONTINUOUS FILE APPRAISER")
        print(f"  Directory : {self.target_dir}")
        print(f"  Model     : {self.model}")
        print(f"  Files     : {total} total, {to_do} need appraisal")
        print(f"{'='*60}\n")

        results = []
        for i, fpath in enumerate(pending, 1):
            rel = fpath.relative_to(self.target_dir)
            print(f"  [{i}/{to_do}] Appraising {rel} ...", end=" ", flush=True)
            try:
                appraisal = await self.appraise_file(fpath)
                results.append(appraisal)
                print(f"${appraisal.dollar_value:,.2f} ({appraisal.category})")
            except Exception as e:
                print(f"FAILED: {e}")

        self._save_ledger()
        return results

    def generate_invoice(self, invoice_id: Optional[str] = None) -> str:
        if not invoice_id:
            invoice_id = f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        items = []
        total = 0.0
        for rel, entry in sorted(self.ledger.items()):
            val = entry.get("dollar_value", 0)
            total += val
            items.append({
                "file": rel,
                "category": entry.get("category", "unknown"),
                "hours": entry.get("estimated_hours", 0),
                "rate": entry.get("hourly_rate", 0),
                "amount": val,
            })

        invoice = {
            "invoice_id": invoice_id,
            "issued": datetime.now(timezone.utc).isoformat(),
            "description": "Agent work — file-level IP appraisal",
            "model_used": self.model,
            "directory": str(self.target_dir),
            "line_items": items,
            "subtotal": round(total, 2),
            "tax_rate": 0.0,
            "total_due": round(total, 2),
            "currency": "USD",
            "status": "draft",
            "notes": "Values estimated by local LLM. Not a legal invoice.",
        }

        path = self.invoice_dir / f"{invoice_id}.json"
        with open(path, "w") as f:
            json.dump(invoice, f, indent=2)

        self._print_invoice(invoice)
        return str(path)

    def _print_invoice(self, inv: dict):
        print(f"\n{'='*70}")
        print(f"  INVOICE: {inv['invoice_id']}")
        print(f"  Date   : {inv['issued']}")
        print(f"  Model  : {inv['model_used']}")
        print(f"{'='*70}")
        print(f"  {'File':<40} {'Category':<15} {'Hours':>6} {'Rate':>8} {'Amount':>10}")
        print(f"  {'-'*40} {'-'*15} {'-'*6} {'-'*8} {'-'*10}")
        for item in inv["line_items"]:
            name = item["file"][:38]
            print(f"  {name:<40} {item['category']:<15} {item['hours']:>6.1f} ${item['rate']:>7.0f} ${item['amount']:>9,.2f}")
        print(f"  {'-'*40} {'-'*15} {'-'*6} {'-'*8} {'-'*10}")
        print(f"  {'':>63} TOTAL: ${inv['total_due']:>9,.2f}")
        print(f"{'='*70}")
        print(f"  Status: {inv['status'].upper()}")
        print(f"  Note: {inv['notes']}")
        print()

    def print_summary(self):
        if not self.ledger:
            print("No appraisals yet.")
            return
        total = sum(e.get("dollar_value", 0) for e in self.ledger.values())
        cats: Dict[str, float] = {}
        for e in self.ledger.values():
            c = e.get("category", "unknown")
            cats[c] = cats.get(c, 0) + e.get("dollar_value", 0)

        print(f"\n  Portfolio Summary: {len(self.ledger)} files = ${total:,.2f}")
        for c, v in sorted(cats.items(), key=lambda x: -x[1]):
            print(f"    {c:<25} ${v:>10,.2f}")
        print()


async def continuous_loop(appraiser: ContinuousAppraiser, interval: int):
    cycle = 0
    while True:
        cycle += 1
        print(f"\n--- Appraisal cycle {cycle} @ {datetime.now().isoformat()} ---")
        await appraiser.run_full_appraisal()
        appraiser.print_summary()
        print(f"Next cycle in {interval}s. Press Ctrl+C to stop.\n")
        await asyncio.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Continuous File Appraiser via Ollama")
    parser.add_argument("--dir", default=".", help="Directory to appraise")
    parser.add_argument("--model", default="llama3", help="Ollama model name")
    parser.add_argument("--interval", type=int, default=300, help="Seconds between cycles (0 = one-shot)")
    parser.add_argument("--invoice", action="store_true", help="Generate invoice after appraisal")
    parser.add_argument("--summary", action="store_true", help="Print summary from existing ledger")
    args = parser.parse_args()

    appraiser = ContinuousAppraiser(target_dir=args.dir, model=args.model)

    if args.summary:
        appraiser.print_summary()
        return

    if args.interval == 0:
        asyncio.run(appraiser.run_full_appraisal())
        if args.invoice:
            appraiser.generate_invoice()
        appraiser.print_summary()
    else:
        try:
            asyncio.run(continuous_loop(appraiser, args.interval))
        except KeyboardInterrupt:
            print("\nStopped.")
            if args.invoice:
                appraiser.generate_invoice()
            appraiser.print_summary()


if __name__ == "__main__":
    main()
