"""A small CLI for the ledger, for humans and the demo scripts.

The MCP server is the primary interface (for agents); this CLI is for a person
inspecting or verifying a ledger by hand. Ledger path via --path or the
EVIDENCE_LEDGER_PATH env var.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from ledger.query import query, stats
from ledger.store import LedgerStore
from ledger.verify import verify_chain


def _store(path: str | None) -> LedgerStore:
    p = path or os.environ.get("EVIDENCE_LEDGER_PATH", "evidence.ledger.jsonl")
    return LedgerStore(Path(p))


def main() -> int:
    parser = argparse.ArgumentParser(prog="evidence-ledger",
                                     description="Inspect and verify an evidence ledger.")
    parser.add_argument("--path", help="Ledger file path (or set EVIDENCE_LEDGER_PATH).")
    sub = parser.add_subparsers(dest="command")

    ap = sub.add_parser("append", help="Append a record.")
    ap.add_argument("actor"); ap.add_argument("action"); ap.add_argument("target")
    ap.add_argument("--details", default="{}", help="JSON object of extra context.")

    sub.add_parser("verify", help="Re-walk the chain and report integrity.")
    sub.add_parser("stats", help="Show ledger statistics.")

    qp = sub.add_parser("query", help="Filter records.")
    qp.add_argument("--actor"); qp.add_argument("--action"); qp.add_argument("--target")

    args = parser.parse_args()
    store = _store(args.path)

    if args.command == "append":
        rec = store.append(args.actor, args.action, args.target, json.loads(args.details))
        print(f"Recorded seq {rec.seq}, receipt {rec.record_hash}")
        return 0
    if args.command == "verify":
        print(verify_chain(store.read_all()).summary())
        return 0
    if args.command == "stats":
        print(json.dumps(stats(store.read_all()).to_dict(), indent=2))
        return 0
    if args.command == "query":
        recs = query(store.read_all(), actor=args.actor, action=args.action, target=args.target)
        for r in recs:
            print(f"  seq {r.seq}: {r.actor} {r.action} {r.target} [{r.record_hash[:12]}...]")
        print(f"{len(recs)} record(s)")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())