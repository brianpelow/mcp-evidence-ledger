"""The evidence record and the canonical hashing that forms the chain.

This module is the integrity core of the whole tool, so it is deliberately
small and strict. Two properties matter above all else:

1. CANONICAL SERIALIZATION. A record must serialize to exactly the same bytes
   every time, on every machine, regardless of dict ordering or whitespace.
   The hash is taken over those bytes, so any ambiguity in serialization would
   make the chain unverifiable. We use JSON with sorted keys and no extra
   whitespace, encoded UTF-8.

2. THE CHAIN. Each record's hash is computed over the previous record's hash
   concatenated with this record's canonical body. Because the previous hash is
   an input, altering any earlier record changes its hash, which invalidates
   every hash after it. Tampering is therefore detectable by re-walking the
   chain -- which is exactly what the verifier does.

The AGENT supplies the semantic fields (actor, action, target, details). The
LEDGER owns the chain fields (seq, prev_hash, timestamp, record_hash). An agent
cannot forge a hash or a sequence number, because it never computes them.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime

# The genesis hash: the prev_hash of the very first record. A fixed, known
# constant so the first link in every ledger chains from the same root.
GENESIS_HASH = "0" * 64


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def canonical_body(
    seq: int,
    timestamp: str,
    actor: str,
    action: str,
    target: str,
    details: dict,
    prev_hash: str,
) -> str:
    """Serialize the hashable body of a record to canonical JSON.

    The record_hash itself is NOT part of the body (it is the output). Every
    other field is, including prev_hash -- that is what chains the records.
    Sorted keys + tight separators make the bytes deterministic.
    """
    body = {
        "seq": seq,
        "timestamp": timestamp,
        "actor": actor,
        "action": action,
        "target": target,
        "details": details,
        "prev_hash": prev_hash,
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_hash(body_json: str) -> str:
    """SHA-256 of the canonical body, hex-encoded."""
    return hashlib.sha256(body_json.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Record:
    """One immutable evidence record in the chain."""

    seq: int
    timestamp: str
    actor: str
    action: str
    target: str
    details: dict
    prev_hash: str
    record_hash: str

    @staticmethod
    def create(
        seq: int,
        actor: str,
        action: str,
        target: str,
        details: dict,
        prev_hash: str,
        timestamp: str | None = None,
    ) -> Record:
        """Build a record and compute its chained hash. The only way to mint one."""
        ts = timestamp or _now()
        body = canonical_body(seq, ts, actor, action, target, details, prev_hash)
        return Record(
            seq=seq,
            timestamp=ts,
            actor=actor,
            action=action,
            target=target,
            details=details,
            prev_hash=prev_hash,
            record_hash=compute_hash(body),
        )

    def recompute_hash(self) -> str:
        """Recompute this record's hash from its own fields.

        The verifier compares this against the stored record_hash. If they
        differ, the record's contents were altered after it was written.
        """
        body = canonical_body(
            self.seq, self.timestamp, self.actor, self.action,
            self.target, self.details, self.prev_hash,
        )
        return compute_hash(body)

    def to_dict(self) -> dict:
        return {
            "seq": self.seq,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "action": self.action,
            "target": self.target,
            "details": self.details,
            "prev_hash": self.prev_hash,
            "record_hash": self.record_hash,
        }

    @staticmethod
    def from_dict(d: dict) -> Record:
        return Record(
            seq=d["seq"],
            timestamp=d["timestamp"],
            actor=d["actor"],
            action=d["action"],
            target=d["target"],
            details=d.get("details", {}),
            prev_hash=d["prev_hash"],
            record_hash=d["record_hash"],
        )