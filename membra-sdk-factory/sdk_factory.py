#!/usr/bin/env python3
"""MEMBRA L0 SDK Factory"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def load_manifest(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def ts_sdk(manifest: Dict[str, Any]) -> str:
    tpl = Path("templates/membra_solana_sdk.ts.template").read_text(encoding="utf-8")
    return (
        tpl.replace("{{RPC}}", manifest["network"]["default_rpc"])
        .replace("{{MIR_PROGRAM}}", manifest["solana"]["programs"]["membra_mir"]["program_id"])
        .replace("{{GATEWAY_PROGRAM}}", manifest["solana"]["programs"]["membra_gateway"]["program_id"])
    )


def py_sdk(manifest: Dict[str, Any]) -> str:
    tpl = Path("templates/membra_l0_sdk.py.template").read_text(encoding="utf-8")
    return (
        tpl.replace("{{NETWORK}}", manifest["network"]["name"])
        .replace("{{RPC}}", manifest["network"]["default_rpc"])
    )


def readme(manifest: Dict[str, Any]) -> str:
    return f"""
# Generated MEMBRA L0 SDK

Generated from `membra.network.json`.

## Network

- Name: {manifest["network"]["name"]}
- Layer: {manifest["network"]["layer"]}
- Environment: {manifest["network"]["environment"]}
- Default RPC: {manifest["network"]["default_rpc"]}

## Generated clients

- `membra_solana_sdk.ts`
- `membra_l0_sdk.py`

## Primitive flow

1. Create MIR locally.
2. Register MIR on Solana devnet through Anchor.
3. M5 node attests inference or compute.
4. Quorum validates the receipt.
5. MCR binds repo proof, memory proof, MIR roots, and collateral score.
6. MEMBRA L0 uses this state for appraisal, rewards, routing, and transaction sponsorship.

## Privacy rule

No raw source code, private prompts, secrets, private keys, or chain-of-thought should be sent on-chain.
Only hashes, summaries, attestations, and settlement metadata are registered.
"""


def main() -> None:
    manifest = load_manifest("membra.network.json")
    out = Path("generated_sdk")
    write(out / "membra_solana_sdk.ts", ts_sdk(manifest))
    write(out / "membra_l0_sdk.py", py_sdk(manifest))
    write(out / "README.md", readme(manifest))
    print("Generated MEMBRA SDK files:")
    print(f"- {out / 'membra_solana_sdk.ts'}")
    print(f"- {out / 'membra_l0_sdk.py'}")
    print(f"- {out / 'README.md'}")


if __name__ == "__main__":
    main()
