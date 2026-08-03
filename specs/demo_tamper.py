"""Demo: prove tamper-evidence by editing the ledger file directly.

Run from the repo root:  uv run python specs/demo_tamper.py

This writes a clean ledger, verifies it, then simulates an attacker editing a
record directly in the file -- and shows the verifier catching it and naming the
exact record. This is the core value of the tool, demonstrated on real state.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ledger.store import LedgerStore
from ledger.verify import verify_chain

LEDGER = Path(__file__).parent / "tamper.ledger.jsonl"


def main() -> int:
    for p in (LEDGER, LEDGER.with_suffix(".jsonl.head")):
        if p.exists():
            p.unlink()

    store = LedgerStore(LEDGER)
    for i in range(5):
        store.append("agent", "access-grant", f"resource-{i}", {"level": "read", "n": i})

    print("A clean 5-record ledger:")
    print("  " + verify_chain(store.read_all()).summary())

    print("\nNow an attacker edits record seq 2 directly in the file,")
    print("changing an access level from 'read' to 'admin' and leaving the hash...\n")

    lines = LEDGER.read_text(encoding="utf-8").splitlines()
    rec = json.loads(lines[2])
    rec["details"]["level"] = "admin"
    lines[2] = json.dumps(rec, sort_keys=True, separators=(",", ":"))
    LEDGER.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Re-verifying...")
    result = verify_chain(store.read_all())
    print("  " + result.summary())
    print("\nThe tampering is caught and located precisely. An agent's evidence")
    print("trail cannot be quietly rewritten after the fact.")
    return 0 if not result.ok else 1  # we EXPECT a break here


if __name__ == "__main__":
    raise SystemExit(main())