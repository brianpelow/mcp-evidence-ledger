"""Golden-file guard: pins the hash format for backward compatibility.

tests/golden/golden.ledger.jsonl is a committed ledger built from fixed inputs
and fixed timestamps. Its record hashes are pinned below. This test asserts that
the current code, reading that committed file, still computes the same hashes and
still verifies the chain.

Why this matters for a cryptographic tool: the record hash is a promise. Every
ledger ever written depends on the exact serialization and hashing rules. If a
change -- however well-intentioned -- alters those rules, every existing ledger
would fail to verify. This test turns that silent, catastrophic break into a
loud, immediate test failure that says exactly what happened.

If you are here because this test failed: you changed the canonical
serialization or the hashing. That is a breaking change to the on-disk format.
Do not "fix" the test by updating the hashes unless you have deliberately
decided to break compatibility and versioned the format accordingly.
"""

from __future__ import annotations

from pathlib import Path

from ledger.store import LedgerStore
from ledger.verify import verify_chain

GOLDEN = Path(__file__).parent / "golden" / "golden.ledger.jsonl"

# Pinned hashes. DO NOT update these to make a failing test pass -- see the
# module docstring. They are the contract.
PINNED_HASHES = [
    "f47b40f16463efb3b49976571149098eb5d7aee6199fa39af43313542c60cd7e",
    "41c28da7d867504af8221d7c43ad3c55a1946b7ae09d23c52a70dee73773ae2c",
    "873f1068ce91b5478e462ccd638885594233454bce2f6dca5373a2e912886824",
    "f8492ab73e31bfba039ed04af2153881c3955481e7cfb5d7b2a4c79c4287eee7",
]


def test_golden_ledger_exists():
    assert GOLDEN.exists(), "the committed golden ledger is missing"


def test_golden_hashes_are_unchanged():
    """Each record's stored hash must match the pinned value exactly."""
    records = LedgerStore(GOLDEN).read_all()
    assert len(records) == len(PINNED_HASHES)
    for rec, pinned in zip(records, PINNED_HASHES, strict=True):
        assert rec.record_hash == pinned, (
            f"seq {rec.seq} hash changed -- the on-disk format or hashing rules "
            f"were altered. This breaks every existing ledger. See this module's "
            f"docstring before touching the pinned values."
        )


def test_golden_hashes_recompute_correctly():
    """Recomputing each record's hash from its fields must match the stored hash."""
    for rec in LedgerStore(GOLDEN).read_all():
        assert rec.recompute_hash() == rec.record_hash


def test_golden_chain_still_verifies():
    """The committed chain must still pass full verification under current code."""
    result = verify_chain(LedgerStore(GOLDEN).read_all())
    assert result.ok, result.summary()
    assert result.records_checked == len(PINNED_HASHES)