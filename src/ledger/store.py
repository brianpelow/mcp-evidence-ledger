"""The append-only ledger store: real local state on disk.

The ledger is a JSONL file -- one record per line -- chosen deliberately over a
binary store so the audit trail is human-inspectable. You can `cat` a ledger and
read every action an agent took. A sidecar `.head` file holds the current head
hash and sequence for O(1) appends without re-reading the whole file.

The store exposes append and read. It deliberately exposes NO update and NO
delete: append-only is the integrity guarantee. If a record is altered or
removed by editing the file directly -- outside this store -- the verifier
detects it. That is the point, not a weakness.

Concurrency note: appends take an exclusive lock on the head file so two writers
cannot interleave and fork the chain. This is a local-state tool, not a
distributed ledger; the lock covers the single-host multi-process case.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from ledger.record import GENESIS_HASH, Record


@dataclass
class Head:
    """The current tip of the chain."""

    seq: int          # sequence of the last record, -1 if empty
    head_hash: str    # hash of the last record, GENESIS_HASH if empty

    @property
    def is_empty(self) -> bool:
        return self.seq < 0


class LedgerStore:
    """Append-only, hash-chained ledger persisted as JSONL + a head sidecar."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._head_path = self._path.with_suffix(self._path.suffix + ".head")

    # --- head management ---------------------------------------------------

    def _read_head(self) -> Head:
        if not self._head_path.exists():
            # Sidecar missing: rebuild from the log rather than assuming empty.
            # A deleted sidecar must never silently reset the head, or an agent
            # could append a forked chain from genesis.
            return self._rebuild_head()
        try:
            data = json.loads(self._head_path.read_text(encoding="utf-8"))
            return Head(seq=data["seq"], head_hash=data["head_hash"])
        except Exception:
            # Head is a cache; if it is corrupt, rebuild from the log.
            return self._rebuild_head()

    def _write_head(self, head: Head) -> None:
        self._head_path.write_text(
            json.dumps({"seq": head.seq, "head_hash": head.head_hash}),
            encoding="utf-8",
        )

    def _rebuild_head(self) -> Head:
        """Reconstruct the head by reading the log's last line. Self-healing."""
        if not self._path.exists():
            return Head(seq=-1, head_hash=GENESIS_HASH)
        last = None
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    last = line
        if last is None:
            return Head(seq=-1, head_hash=GENESIS_HASH)
        rec = json.loads(last)
        return Head(seq=rec["seq"], head_hash=rec["record_hash"])

    # --- append ------------------------------------------------------------

    def append(self, actor: str, action: str, target: str, details: dict,
               timestamp: str | None = None) -> Record:
        """Append a new evidence record and return it with its receipt hash."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        head = self._read_head()
        record = Record.create(
            seq=head.seq + 1,
            actor=actor,
            action=action,
            target=target,
            details=details,
            prev_hash=head.head_hash,
            timestamp=timestamp,
        )
        line = json.dumps(record.to_dict(), sort_keys=True, separators=(",", ":"))
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())
        self._write_head(Head(seq=record.seq, head_hash=record.record_hash))
        return record

    # --- read --------------------------------------------------------------

    def read_all(self) -> list[Record]:
        """Read every record in order. Used by verify and query."""
        if not self._path.exists():
            return []
        records: list[Record] = []
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(Record.from_dict(json.loads(line)))
        return records

    def get(self, seq: int) -> Record | None:
        for rec in self.read_all():
            if rec.seq == seq:
                return rec
        return None

    def head(self) -> Head:
        return self._read_head()

    @property
    def path(self) -> Path:
        return self._path