"""The `chronoswarm` command-line entry point."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from .fitness import FitnessWeights
from .governor import GeneticLayoutGovernor
from .receipts import list_receipts
from .scheduler import ChronoScheduler, SchedulerThresholds
from .store import WorkflowStore
from .tmuxctl import TmuxController, TmuxError


def _db_path(data_dir: str) -> str:
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "chronoswarm.db")


def _print(obj) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def cmd_start_session(args: argparse.Namespace) -> int:
    tmux = TmuxController(args.session)
    store = WorkflowStore(_db_path(args.data_dir))
    try:
        first_pane_id = tmux.new_session(width=args.width, height=args.height)
        now = time.time()
        record = store.register_pane(first_pane_id, args.session, role=args.role, now=now)
        _print({"pane_id": record.pane_id, "session_name": record.session_name, "state": record.state})
    finally:
        store.close()
    return 0


def cmd_split(args: argparse.Namespace) -> int:
    tmux = TmuxController(args.session)
    store = WorkflowStore(_db_path(args.data_dir))
    try:
        new_pane_id = tmux.split_window(
            args.pane_id, vertical=args.vertical, size_pct=args.size_pct
        )
        now = time.time()
        record = store.register_pane(new_pane_id, args.session, role=args.role, now=now)
        _print({"pane_id": record.pane_id, "session_name": record.session_name, "state": record.state})
    finally:
        store.close()
    return 0


def cmd_list_panes(args: argparse.Namespace) -> int:
    tmux = TmuxController(args.session)
    store = WorkflowStore(_db_path(args.data_dir))
    try:
        panes = []
        for pane in sorted(tmux.list_panes(), key=lambda p: p.left):
            record = store.get_pane(pane.pane_id)
            panes.append(
                {
                    "pane_id": pane.pane_id,
                    "active": pane.active,
                    "left": pane.left,
                    "width": pane.width,
                    "height": pane.height,
                    "state": record.state if record else None,
                    "role": record.role if record else None,
                }
            )
        _print(panes)
    finally:
        store.close()
    return 0


def cmd_send_keys(args: argparse.Namespace) -> int:
    tmux = TmuxController(args.session)
    store = WorkflowStore(_db_path(args.data_dir))
    try:
        tmux.send_keys(args.pane_id, args.keys, enter=not args.no_enter)
        now = time.time()
        store.touch_activity(args.pane_id, now)
        _print({"pane_id": args.pane_id, "sent": args.keys, "activity_ts": now})
    finally:
        store.close()
    return 0


def cmd_breed(args: argparse.Namespace) -> int:
    tmux = TmuxController(args.session)
    store = WorkflowStore(_db_path(args.data_dir))
    try:
        governor = GeneticLayoutGovernor(tmux, store, FitnessWeights())
        result = governor.breed_and_apply(
            generations=args.generations, population_size=args.population, seed=args.seed
        )
        _print(result)
    finally:
        store.close()
    return 0


def cmd_tick(args: argparse.Namespace) -> int:
    tmux = TmuxController(args.session)
    store = WorkflowStore(_db_path(args.data_dir))
    try:
        scheduler = ChronoScheduler(store, SchedulerThresholds())
        transitions = scheduler.tick(tmux)
        _print(transitions)
    finally:
        store.close()
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    store = WorkflowStore(_db_path(args.data_dir))
    try:
        if args.pane_id:
            record = store.get_pane(args.pane_id)
            if record is None:
                print(f"no such pane: {args.pane_id}", file=sys.stderr)
                return 1
            _print(record.__dict__)
        else:
            _print([r.__dict__ for r in store.list_panes(session_name=args.session)])
    finally:
        store.close()
    return 0


def cmd_receipts(args: argparse.Namespace) -> int:
    store = WorkflowStore(_db_path(args.data_dir))
    try:
        receipts = list_receipts(store, pane_id=args.pane_id)
        _print([r.to_dict() for r in receipts])
    finally:
        store.close()
    return 0


def cmd_kill_session(args: argparse.Namespace) -> int:
    tmux = TmuxController(args.session)
    tmux.kill_session()
    _print({"killed": args.session})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chronoswarm")
    parser.add_argument("--data-dir", default="./.chronoswarm-data")
    parser.add_argument("--session", required=True, help="tmux session name")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("start-session")
    p.add_argument("--width", type=int, default=200)
    p.add_argument("--height", type=int, default=50)
    p.add_argument("--role", default="unlabeled")
    p.set_defaults(func=cmd_start_session)

    p = sub.add_parser("split")
    p.add_argument("--pane-id", required=True)
    p.add_argument("--vertical", action="store_true")
    p.add_argument("--size-pct", type=int, default=None)
    p.add_argument("--role", default="unlabeled")
    p.set_defaults(func=cmd_split)

    p = sub.add_parser("list-panes")
    p.set_defaults(func=cmd_list_panes)

    p = sub.add_parser("send-keys")
    p.add_argument("--pane-id", required=True)
    p.add_argument("--keys", required=True)
    p.add_argument("--no-enter", action="store_true")
    p.set_defaults(func=cmd_send_keys)

    p = sub.add_parser("breed")
    p.add_argument("--generations", type=int, default=30)
    p.add_argument("--population", type=int, default=20)
    p.add_argument("--seed", type=int, default=None)
    p.set_defaults(func=cmd_breed)

    p = sub.add_parser("tick")
    p.set_defaults(func=cmd_tick)

    p = sub.add_parser("status")
    p.add_argument("--pane-id", default=None)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("receipts")
    p.add_argument("--pane-id", default=None)
    p.set_defaults(func=cmd_receipts)

    p = sub.add_parser("kill-session")
    p.set_defaults(func=cmd_kill_session)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except TmuxError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
