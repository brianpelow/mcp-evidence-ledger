"""The chain verifier: proves integrity, or pinpoints the first break.

Verification re-walks the entire chain from genesis and checks two things at
every record:

1. CONTENT INTEGRITY. The record's stored hash must equal the hash recomputed
   from its own fields. If they differ, the record's contents were altered
   after it was written.

2. CHAIN LINKAGE. The record's prev_hash must equal the previous record's
   stored hash, and its seq must be exactly one more than the previous. If not,
   a record was inserted, removed, or reordered.

The verifier reports the FIRST break and its cause, because in a hash chain a
break at position N invalidates everything after it -- so the first break is the
actionable one. A clean result is a positive proof: every record is intact and
correctly linked, from genesis to head.
"""

from __future__ import annotations

from dataclasses import dataclass

from ledger.record import GENESIS_HASH, Record


@dataclass
class VerifyResult:
    """The outcome of verifying a ledger."""

    ok: bool
    records_checked: int
    break_seq: int | None = None       # sequence of the first broken record
    break_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "records_checked": self.records_checked,
            "break_seq": self.break_seq,
            "break_reason": self.break_reason,
        }

    def summary(self) -> str:
        if self.ok:
            return (
                f"INTACT: {self.records_checked} records verified, "
                f"chain unbroken from genesis to head."
            )
        return (
            f"TAMPERED: chain broken at seq {self.break_seq} -- {self.break_reason} "
            f"({self.records_checked} records checked before the break)."
        )


def verify_chain(records: list[Record]) -> VerifyResult:
    """Re-walk the chain and return the first integrity failure, if any."""
    if not records:
        return VerifyResult(ok=True, records_checked=0)

    prev_hash = GENESIS_HASH
    expected_seq = 0

    for i, rec in enumerate(records):
        # 1. Sequence must be contiguous and ascending from 0.
        if rec.seq != expected_seq:
            return VerifyResult(
                ok=False,
                records_checked=i,
                break_seq=rec.seq,
                break_reason=(
                    f"sequence gap or reorder: expected seq {expected_seq}, "
                    f"found {rec.seq} (a record was inserted, removed, or moved)"
                ),
            )

        # 2. Linkage: this record must point at the previous record's hash.
        if rec.prev_hash != prev_hash:
            return VerifyResult(
                ok=False,
                records_checked=i,
                break_seq=rec.seq,
                break_reason=(
                    "broken link: prev_hash does not match the prior record's "
                    "hash (a prior record was altered or a record was removed)"
                ),
            )

        # 3. Content integrity: the stored hash must match the recomputed hash.
        recomputed = rec.recompute_hash()
        if recomputed != rec.record_hash:
            return VerifyResult(
                ok=False,
                records_checked=i,
                break_seq=rec.seq,
                break_reason=(
                    "content altered: this record's fields were changed after "
                    "it was written (stored hash does not match its contents)"
                ),
            )

        prev_hash = rec.record_hash
        expected_seq += 1

    return VerifyResult(ok=True, records_checked=len(records))