"""Query and stats over the ledger. Read-only, deterministic."""

from __future__ import annotations

from dataclasses import dataclass

from ledger.record import Record
from ledger.verify import verify_chain


@dataclass
class LedgerStats:
    total_records: int
    actors: dict[str, int]
    actions: dict[str, int]
    head_hash: str
    head_seq: int
    integrity_ok: bool
    integrity_note: str

    def to_dict(self) -> dict:
        return {
            "total_records": self.total_records,
            "actors": self.actors,
            "actions": self.actions,
            "head_hash": self.head_hash,
            "head_seq": self.head_seq,
            "integrity_ok": self.integrity_ok,
            "integrity_note": self.integrity_note,
        }


def query(
    records: list[Record],
    actor: str | None = None,
    action: str | None = None,
    target: str | None = None,
    since: str | None = None,
    until: str | None = None,
) -> list[Record]:
    """Filter records by any combination of fields. All filters are AND-ed."""
    out = records
    if actor is not None:
        out = [r for r in out if r.actor == actor]
    if action is not None:
        out = [r for r in out if r.action == action]
    if target is not None:
        out = [r for r in out if r.target == target]
    if since is not None:
        out = [r for r in out if r.timestamp >= since]
    if until is not None:
        out = [r for r in out if r.timestamp <= until]
    return out


def stats(records: list[Record]) -> LedgerStats:
    """Compute deterministic summary stats plus a live integrity check."""
    actors: dict[str, int] = {}
    actions: dict[str, int] = {}
    for r in records:
        actors[r.actor] = actors.get(r.actor, 0) + 1
        actions[r.action] = actions.get(r.action, 0) + 1

    v = verify_chain(records)
    head = records[-1] if records else None

    return LedgerStats(
        total_records=len(records),
        actors=dict(sorted(actors.items())),
        actions=dict(sorted(actions.items())),
        head_hash=head.record_hash if head else "0" * 64,
        head_seq=head.seq if head else -1,
        integrity_ok=v.ok,
        integrity_note=v.summary(),
    )