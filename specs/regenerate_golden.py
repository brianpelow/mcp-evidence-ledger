"""Regenerate the golden ledger fixture.

WARNING: only run this if you have DELIBERATELY changed the on-disk format
and intend to break backward compatibility. Regenerating changes the pinned
hashes, which must then be updated in tests/test_golden.py by hand. Under
normal development you should never need to run this -- the golden test
exists precisely to catch unintended changes to the hashing.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from ledger.store import LedgerStore

# Fixed inputs + fixed timestamps => a deterministic golden ledger.
# If the hashing or serialization ever changes, these committed hashes stop
# matching and the golden test fails, flagging a backward-compatibility break.
golden = Path("tests/golden/golden.ledger.jsonl")
for p in (golden, golden.with_suffix(".jsonl.head")):
    if p.exists(): p.unlink()
golden.parent.mkdir(parents=True, exist_ok=True)

store = LedgerStore(golden)
fixtures = [
    ("deploy-agent", "deploy", "payments-api", {"version": "4.2.0", "env": "prod"}, "2026-01-01T00:00:00+00:00"),
    ("deploy-agent", "config-change", "payments-api", {"key": "timeout", "value": "30s"}, "2026-01-01T00:01:00+00:00"),
    ("data-agent", "data-export", "customer-db", {"rows": 1200}, "2026-01-01T00:02:00+00:00"),
    ("deploy-agent", "rollback", "payments-api", {"to_version": "4.1.9"}, "2026-01-01T00:03:00+00:00"),
]
for actor, action, target, details, ts in fixtures:
    store.append(actor, action, target, details, timestamp=ts)

# Remove the head sidecar so only the ledger file is the golden artifact
head = golden.with_suffix(".jsonl.head")
if head.exists(): head.unlink()

print("Golden ledger written. Pinned hashes:")
for rec in store.read_all():
    print(f"  seq {rec.seq}: {rec.record_hash}")