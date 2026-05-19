#!/usr/bin/env python3
"""Membra Model Hub CLI — interact with the decentralized model network."""
from __future__ import annotations

import os
import sys
import time
from typing import Any

import click
import httpx

API_KEY = os.getenv("MEMBRA_API_KEY", "dev-key-change-me")
DEFAULT_REGISTRY = os.getenv("MEMBRA_REGISTRY", "http://localhost:8765")


def _client() -> httpx.Client:
    return httpx.Client(
        timeout=30.0,
        headers={"authorization": f"Bearer {API_KEY}"},
    )


@click.group()
def cli() -> None:
    """Membra Decentralized Model Hub CLI"""
    pass


@cli.command()
@click.option("--registry", default=DEFAULT_REGISTRY, help="Registry/Router URL")
def list_models(registry: str) -> None:
    """List models available on the network."""
    with _client() as c:
        r = c.get(f"{registry}/models")
    if r.status_code != 200:
        click.echo(f"Error: {r.status_code} {r.text}", err=True)
        sys.exit(1)
    models: list[dict[str, Any]] = r.json()
    if not models:
        click.echo("No models found on the network.")
        return
    click.echo(f"{'MODEL ID':<30} {'FORMAT':<12} {'PARAMS':<8} {'SHARDS':<8} TAGS")
    click.echo("-" * 80)
    for m in models:
        shards = len(m.get("shards", []))
        click.echo(
            f"{m['model_id']:<30} {m.get('format',''):<12} "
            f"{m.get('parameters',''):<8} {shards:<8} {', '.join(m.get('tags', []))}"
        )


@cli.command()
@click.option("--registry", default=DEFAULT_REGISTRY, help="Registry/Router URL")
def list_nodes(registry: str) -> None:
    """List active peer nodes on the network."""
    with _client() as c:
        r = c.get(f"{registry}/nodes")
    if r.status_code != 200:
        click.echo(f"Error: {r.status_code} {r.text}", err=True)
        sys.exit(1)
    nodes: list[dict[str, Any]] = r.json()
    if not nodes:
        click.echo("No peers found on the network.")
        return
    click.echo(f"{'NODE ID':<30} {'HOST':<20} {'HEALTH':<10} {'JOBS':<6} MODELS")
    click.echo("-" * 90)
    for n in nodes:
        models = ", ".join(n.get("caps", {}).get("models_hosted", []))
        click.echo(
            f"{n['node_id']:<30} {n.get('hostname',''):<20} "
            f"{n.get('health',''):<10} {n.get('active_jobs',0):<6} {models}"
        )


@cli.command()
@click.argument("model_id")
@click.argument("prompt")
@click.option("--registry", default=DEFAULT_REGISTRY, help="Registry/Router URL")
@click.option("--max-tokens", default=256, help="Max tokens to generate")
@click.option("--temperature", default=0.7, help="Sampling temperature")
@click.option("--system", default=None, help="System prompt")
def infer(
    model_id: str,
    prompt: str,
    registry: str,
    max_tokens: int,
    temperature: float,
    system: str | None,
) -> None:
    """Run inference via the decentralized network."""
    payload = {
        "model_id": model_id,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
        "system_prompt": system,
    }
    with _client() as c:
        r = c.post(f"{registry}/inference", json=payload)
    if r.status_code != 200:
        click.echo(f"Error: {r.status_code} {r.text}", err=True)
        sys.exit(1)
    data = r.json()
    task_id = data["task_id"]
    click.echo(f"Task submitted: {task_id}")
    click.echo("Polling for result...")
    # Poll
    with _client() as c:
        for _ in range(60):
            r = c.get(f"{registry}/inference/{task_id}")
            if r.status_code == 200:
                task = r.json()
                if task["status"] in ("success", "error", "timeout"):
                    click.echo("\n--- Result ---")
                    result = task.get("result") or {}
                    output = result.get("output") or "(no output)"
                    click.echo(output)
                    click.echo(f"\nStatus: {task['status']} | Node: {result.get('node_id','?')} | Proof: {result.get('proof_hash','')[:16]}...")
                    return
            time.sleep(2)
    click.echo("Timed out waiting for result.", err=True)


@cli.command()
@click.argument("model_id")
@click.option("--description", default="", help="Model description")
@click.option("--tags", default="", help="Comma-separated tags")
@click.option("--parameters", default="", help="Parameter count (e.g. 7B)")
@click.option("--quantization", default="", help="Quantization (e.g. Q4_K_M)")
@click.option("--registry", default=DEFAULT_REGISTRY, help="Registry URL")
def publish(
    model_id: str,
    description: str,
    tags: str,
    parameters: str,
    quantization: str,
    registry: str,
) -> None:
    """Publish a model card to the decentralized registry."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    payload = {
        "model_id": model_id,
        "description": description,
        "tags": tag_list,
        "parameters": parameters,
        "quantization": quantization,
        "format": "ollama",
    }
    with _client() as c:
        r = c.post(f"{registry}/models", json=payload)
    if r.status_code != 200:
        click.echo(f"Error: {r.status_code} {r.text}", err=True)
        sys.exit(1)
    click.echo(f"Published: {r.json()}")


@cli.command()
@click.option("--models", required=True, help="Comma-separated Ollama models to host")
@click.option("--port", default=8766, help="Worker HTTP port")
@click.option("--bootstrap", default="", help="Comma-separated bootstrap peer URLs")
def worker(models: str, port: int, bootstrap: str) -> None:
    """Start a model worker node (wraps worker_node.py)."""
    import subprocess
    cmd = [sys.executable, "worker_node.py", "--models", models, "--port", str(port)]
    if bootstrap:
        cmd.extend(["--bootstrap", bootstrap])
    subprocess.run(cmd)


@cli.command()
@click.option("--port", default=8765, help="Registry/Router HTTP port")
@click.option("--bootstrap", default="", help="Comma-separated bootstrap peer URLs")
def registry(port: int, bootstrap: str) -> None:
    """Start a registry + inference router node."""
    import subprocess
    env = os.environ.copy()
    env["MEMBRA_API_PORT"] = str(port)
    if bootstrap:
        env["MEMBRA_BOOTSTRAP_PEERS"] = bootstrap
    cmd = [sys.executable, "-m", "uvicorn", "inference_router:app", "--host", "0.0.0.0", "--port", str(port)]
    subprocess.run(cmd, env=env)


if __name__ == "__main__":
    cli()
