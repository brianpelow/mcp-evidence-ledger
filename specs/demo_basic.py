"""Demo: record a sequence of agent actions and verify the chain.

Run from the repo root:  uv run python specs/demo_basic.py

Writes a real ledger to specs/basic.ledger.jsonl so you can inspect it
afterward -- open the file and read the audit trail yourself.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ledger.store import LedgerStore
from ledger.verify import verify_chain

LEDGER = Path(__file__).parent / "basic.ledger.jsonl"


def main() -> int:
    for p in (LEDGER, LEDGER.with_suffix(".jsonl.head")):
        if p.exists():
            p.unlink()

    store = LedgerStore(LEDGER)

    print("Recording a sequence of agent actions...\n")
    events = [
        ("deploy-agent", "deploy", "payments-api", {"version": "4.2.0", "env": "prod"}),
        ("deploy-agent", "config-change", "payments-api", {"key": "timeout", "value": "30s"}),
        ("data-agent", "data-export", "customer-db", {"rows": 1200, "purpose": "monthly-report"}),
        ("deploy-agent", "rollback", "payments-api", {"to_version": "4.1.9", "reason": "latency spike"}),
    ]
    for actor, action, target, details in events:
        rec = store.append(actor, action, target, details)
        print(f"  seq {rec.seq}: {actor} {action} {target}")
        print(f"          receipt {rec.record_hash[:24]}...")

    print("\nVerifying the chain...")
    result = verify_chain(store.read_all())
    print("  " + result.summary())

    print(f"\nThe full audit trail is at {LEDGER}")
    print("Open it -- every action an agent took, each cryptographically bound to the last.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())