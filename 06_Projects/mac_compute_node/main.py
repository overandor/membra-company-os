#!/usr/bin/env python3
"""
MEMBRA L3 — Multi-Chain Autonomous Node Entry Point
Solana + Sui + Berachain | LLM Consensus | P2P Agent Network

Usage:
    python main.py               # Start L3 node
    python main.py --cli         # Terminal dashboard
    python main.py --l3          # Full L3 multi-chain mode
    python main.py --dashboard   # Web dashboard only
"""
import argparse
import asyncio
import json
import os
import sys
import time

import psutil
import yaml
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout

from dashboard.app import run_dashboard
from membra_l3 import MembraL3Node

console = Console()

BRAND = """
[bold green]
╔══════════════════════════════════════════════════════════════╗
║  ███╗   ███╗ ███████╗ ███╗   ███╗ ██████╗  ██████╗   █████╗   ║
║  ████╗ ████║ ██╔════╝ ████╗ ████║ ██╔══██╗ ██╔══██╗ ██╔══██╗  ║
║  ██╔████╔██║ █████╗   ██╔████╔██║ ██████╔╝ ██████╔╝ ███████║  ║
║  ██║╚██╔╝██║ ██╔══╝   ██║╚██╔╝██║ ██╔══██╗ ██╔══██╗ ██╔══██║  ║
║  ██║ ╚═╝ ██║ ███████╗ ██║ ╚═╝ ██║ ██████╔╝ ██╔══██╗ ██║  ██║  ║
║  ╚═╝     ╚═╝ ╚══════╝ ╚═╝     ╚═╝ ╚═════╝  ╚═╝  ╚═╝ ╚═╝  ╚═╝  ║
╠══════════════════════════════════════════════════════════════╣
║  MEMBRA L3 — SOLANA + SUI + BERACHAIN + LLM CONSENSUS       ║
╚══════════════════════════════════════════════════════════════╝
[/bold green]
"""


class MembraL3CLI:
    """Interactive terminal dashboard for Membra L3."""

    def __init__(self, config_path: str = None):
        self.node = MembraL3Node(config_path)

    async def run_cli(self):
        console.print(BRAND)
        s = self.node.get_status()
        console.print(f"[bold cyan]Agent:[/bold cyan]   {s['agent_id']}")
        console.print(f"[bold cyan]Chains:[/bold cyan]  Solana devnet | Sui testnet | Berachain bArtio")
        console.print(f"[bold cyan]SOL:[/bold cyan]     {s['solana_balance']:.4f}")
        console.print()

        with Live(self._build_layout(), refresh_per_second=2) as live:
            # Start L3 node in background
            asyncio.create_task(self.node.run())

            try:
                while self.node.running:
                    live.update(self._build_layout())
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                self.node.running = False

    def _build_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(Layout(name="header", size=3), Layout(name="main"))
        layout["main"].split_row(Layout(name="left"), Layout(name="right"), Layout(name="center"))
        layout["left"].split_column(Layout(name="resources"), Layout(name="consensus"))
        layout["right"].split_column(Layout(name="chains"), Layout(name="earnings"))
        layout["center"].split_column(Layout(name="p2p"), Layout(name="trades"))

        s = self.node.get_status()

        # Header
        header = Panel(
            f"[bold green]MEMBRA L3[/bold green] | "
            f"Agent: {s['agent_id']} | "
            f"Ops: {s['ops_processed']:,} | "
            f"Peers: {s['p2p']['peers']} | "
            f"Consensus: {s['consensus']['finalized']} | "
            f"Press Ctrl+C to stop",
            style="green",
        )
        layout["header"].update(header)

        # Resources
        r = psutil.virtual_memory()
        res_table = Table(show_header=False, box=None)
        res_table.add_column("Resource", style="cyan")
        res_table.add_column("Value", style="white")
        res_table.add_row("CPU", f"{psutil.cpu_count()} cores @ {psutil.cpu_percent(interval=0.1):.0f}%")
        res_table.add_row("Memory", f"{r.used//(1024**3)}/{r.total//(1024**3)} GB ({r.percent:.0f}%)")
        res_table.add_row("Pending Ops", str(s['pending_ops']))
        layout["resources"].update(Panel(res_table, title="[bold]Resources[/bold]"))

        # Consensus
        c = s['consensus']
        cons_table = Table(show_header=False, box=None)
        cons_table.add_column("Metric", style="cyan")
        cons_table.add_column("Value", style="white")
        cons_table.add_row("Rounds", str(c['total_rounds']))
        cons_table.add_row("Finalized", f"[green]{c['finalized']}[/green]")
        cons_table.add_row("Finality ms", str(c.get('avg_finality_ms', 0)))
        layout["consensus"].update(Panel(cons_table, title="[bold]LLM Consensus[/bold]"))

        # Chains
        m = s['multi_chain']
        chain_table = Table(show_header=False, box=None)
        chain_table.add_column("Chain", style="cyan")
        chain_table.add_column("Status", style="white")
        for receipt in m.get('recent_receipts', []):
            color = "green" if receipt.get('status') == 'confirmed' else "red"
            chain_table.add_row(receipt['chain'], f"[{color}]{receipt['status']}[/]")
        chain_table.add_row("Receipts", str(m.get('total_receipts', 0)))
        layout["chains"].update(Panel(chain_table, title="[bold]Multi-Chain[/bold]"))

        # Earnings
        b = s['bridge']
        earn_table = Table(show_header=False, box=None)
        earn_table.add_column("Metric", style="cyan")
        earn_table.add_column("Value", style="white")
        earn_table.add_row("Total Rewarded", f"[bold green]{b.get('total_rewarded', 0):.6f} {b.get('currency', 'COMPUTE')}[/]")
        earn_table.add_row("Pending", str(b.get('pending_rewards', 0)))
        earn_table.add_row("SOL", f"{s['solana_balance']:.4f}")
        earn_table.add_row("Token", f"{s['token_balance']:,.0f}")
        layout["earnings"].update(Panel(earn_table, title="[bold]Earnings[/bold]"))

        # P2P
        p = s['p2p']
        p2p_table = Table(show_header=False, box=None)
        p2p_table.add_column("Metric", style="cyan")
        p2p_table.add_column("Value", style="white")
        p2p_table.add_row("Peers", str(p['peers']))
        p2p_table.add_row("WS Conns", str(p['ws_connections']))
        p2p_table.add_row("Sent", str(p['messages_sent']))
        p2p_table.add_row("Received", str(p['messages_received']))
        layout["p2p"].update(Panel(p2p_table, title="[bold]P2P Network[/bold]"))

        # Trades
        trade_table = Table(show_header=False, box=None)
        trade_table.add_column("Metric", style="cyan")
        trade_table.add_column("Value", style="white")
        trade_table.add_row("Trades", str(s['trades']))
        trade_table.add_row("Token Deployed", "Yes" if s['token_deployed'] else "No")
        trade_table.add_row("Token Minted", "Yes" if s['token_minted'] else "No")
        layout["trades"].update(Panel(trade_table, title="[bold]Trading[/bold]"))

        return layout


def main():
    parser = argparse.ArgumentParser(description="Membra L3 Multi-Chain Node")
    parser.add_argument("--cli", action="store_true", help="Terminal dashboard mode")
    parser.add_argument("--l3", action="store_true", help="Full L3 multi-chain mode")
    parser.add_argument("--dashboard", action="store_true", help="Web dashboard only")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    args = parser.parse_args()

    if args.dashboard:
        run_dashboard()
        return

    cli = MembraL3CLI(args.config)

    if args.cli or args.l3:
        try:
            asyncio.run(cli.run_cli())
        except KeyboardInterrupt:
            console.print("\n[bold red]Shutdown complete.[/bold red]")
    else:
        console.print(BRAND)
        console.print("[bold cyan]Starting Membra L3...[/bold cyan]")
        console.print("Use --cli for terminal dashboard or --l3 for full mode")

        async def run_simple():
            await cli.node.run()

        try:
            asyncio.run(run_simple())
        except KeyboardInterrupt:
            cli.node.running = False
            console.print("\n[bold red]Goodbye.[/bold red]")


if __name__ == "__main__":
    main()
