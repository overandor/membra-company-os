#!/usr/bin/env python3
"""DeCloud CLI — Deploy, update, and inspect decentralized apps.

Usage:
  decloud deploy <app_id> <directory> [--owner OWNER] [--gateway URL]
  decloud update <app_id> <directory> [--owner OWNER] [--gateway URL]
  decloud delete <app_id> [--owner OWNER] [--gateway URL]
  decloud status <app_id> [--gateway URL]
  decloud list [--gateway URL]
  decloud nodes [--gateway URL]
"""
import argparse
import os
import sys
from pathlib import Path
import httpx

DEFAULT_GATEWAY = os.environ.get("DECLOUD_GATEWAY", "http://127.0.0.1:8080")


def _client() -> httpx.Client:
    return httpx.Client(base_url=DEFAULT_GATEWAY, timeout=30.0)


def cmd_deploy(args):
    directory = Path(args.directory).resolve()
    if not directory.is_dir():
        print(f"Error: {directory} is not a directory", file=sys.stderr)
        sys.exit(1)
    with _client() as client:
        r = client.post("/deploy", json={
            "app_id": args.app_id,
            "owner": args.owner,
            "bundle_dir": str(directory),
            "metadata": {},
        })
    if r.status_code != 200:
        print(f"Deploy failed: {r.status_code} {r.text}", file=sys.stderr)
        sys.exit(1)
    data = r.json()
    print(f"Deployed {args.app_id}")
    print(f"  CID: {data['cid']}")
    print(f"  Status: {data['status']}")
    print(f"  URL: {DEFAULT_GATEWAY}/proxy/{args.app_id}/")


def cmd_update(args):
    directory = Path(args.directory).resolve()
    if not directory.is_dir():
        print(f"Error: {directory} is not a directory", file=sys.stderr)
        sys.exit(1)
    with _client() as client:
        r = client.post("/update", json={
            "app_id": args.app_id,
            "owner": args.owner,
            "bundle_dir": str(directory),
            "metadata": {},
        })
    if r.status_code != 200:
        print(f"Update failed: {r.status_code} {r.text}", file=sys.stderr)
        sys.exit(1)
    data = r.json()
    print(f"Updated {args.app_id}")
    print(f"  CID: {data['cid']}")
    print(f"  Status: {data['status']}")


def cmd_delete(args):
    with _client() as client:
        r = client.post("/delete", json={
            "app_id": args.app_id,
            "owner": args.owner,
        })
    if r.status_code != 200:
        print(f"Delete failed: {r.status_code} {r.text}", file=sys.stderr)
        sys.exit(1)
    print(f"Deleted {args.app_id}")


def cmd_status(args):
    with _client() as client:
        r = client.get(f"/apps/{args.app_id}")
    if r.status_code != 200:
        print(f"Status fetch failed: {r.status_code} {r.text}", file=sys.stderr)
        sys.exit(1)
    data = r.json()
    rec = data.get("record", {})
    print(f"App: {args.app_id}")
    print(f"  CID:    {rec.get('cid')}")
    print(f"  Owner:  {rec.get('owner')}")
    print(f"  Action: {rec.get('action')}")
    print(f"  Nodes:  {', '.join(data.get('nodes', [])) or 'None'}")


def cmd_list(args):
    with _client() as client:
        r = client.get("/apps")
    if r.status_code != 200:
        print(f"List failed: {r.status_code} {r.text}", file=sys.stderr)
        sys.exit(1)
    apps = r.json().get("apps", [])
    if not apps:
        print("No apps deployed")
        return
    print(f"{'App ID':<20} {'CID':<64} {'Action'}")
    for a in apps:
        rec = a.get("latest", {})
        print(f"{a['app_id']:<20} {rec.get('cid', ''):<64} {rec.get('action', '')}")


def cmd_nodes(args):
    with _client() as client:
        r = client.get("/nodes")
    if r.status_code != 200:
        print(f"Nodes fetch failed: {r.status_code} {r.text}", file=sys.stderr)
        sys.exit(1)
    nodes = r.json().get("nodes", [])
    if not nodes:
        print("No nodes registered")
        return
    print(f"{'Node ID':<20} {'Endpoint':<30} {'Region':<12} {'Health':<10} {'Apps'}")
    for n in nodes:
        apps = ",".join(n.get("active_apps", [])) or "-"
        print(f"{n['node_id']:<20} {n['endpoint']:<30} {n.get('region',''):<12} "
              f"{n.get('health',''):<10} {apps}")


def main():
    global DEFAULT_GATEWAY
    parser = argparse.ArgumentParser(prog="decloud", description="DeCloud CLI")
    parser.add_argument("--gateway", default=DEFAULT_GATEWAY, help="Gateway URL")
    sub = parser.add_subparsers(dest="command", required=True)

    deploy_p = sub.add_parser("deploy")
    deploy_p.add_argument("app_id")
    deploy_p.add_argument("directory")
    deploy_p.add_argument("--owner", default="anonymous")
    deploy_p.set_defaults(func=cmd_deploy)

    update_p = sub.add_parser("update")
    update_p.add_argument("app_id")
    update_p.add_argument("directory")
    update_p.add_argument("--owner", default="anonymous")
    update_p.set_defaults(func=cmd_update)

    delete_p = sub.add_parser("delete")
    delete_p.add_argument("app_id")
    delete_p.add_argument("--owner", default="anonymous")
    delete_p.set_defaults(func=cmd_delete)

    status_p = sub.add_parser("status")
    status_p.add_argument("app_id")
    status_p.set_defaults(func=cmd_status)

    list_p = sub.add_parser("list")
    list_p.set_defaults(func=cmd_list)

    nodes_p = sub.add_parser("nodes")
    nodes_p.set_defaults(func=cmd_nodes)

    args = parser.parse_args()
    DEFAULT_GATEWAY = args.gateway
    args.func(args)


if __name__ == "__main__":
    main()
