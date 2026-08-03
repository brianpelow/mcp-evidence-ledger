"""Optional governance-typed layer.

The ledger core is generic: it records any actor doing any action. This module
is a thin, opt-in convenience layer that maps a record's action onto the shared
governance failure taxonomy used across the portfolio (the same classes the
gateway enforces and the chaos engine injects), so an evidence ledger can be
read through a governance lens without the core depending on any of it.

Nothing here touches the chain or the hashing. It is pure interpretation over
records the ledger already holds. Use it or ignore it; the ledger does not care.
"""

from __future__ import annotations

from ledger.record import Record

# A record's action string, mapped to the governance concern it evidences.
# This is interpretation, not enforcement -- it annotates, it does not gate.
ACTION_TO_CONCERN: dict[str, str] = {
    "deploy": "deployment_authorization",
    "config-change": "change_management",
    "rollback": "change_management",
    "model-swap": "model_registry",
    "access-grant": "access_control",
    "data-export": "data_governance",
    "control-disable": "control_health",
}


def concern_for(record: Record) -> str:
    """The governance concern a record evidences, or 'general' if unmapped."""
    return ACTION_TO_CONCERN.get(record.action, "general")


def annotate(records: list[Record]) -> list[dict]:
    """Return each record as a dict with its governance concern attached."""
    out = []
    for r in records:
        d = r.to_dict()
        d["governance_concern"] = concern_for(r)
        out.append(d)
    return out


def concern_coverage(records: list[Record]) -> dict[str, int]:
    """Count records by governance concern -- what is this ledger evidence OF."""
    counts: dict[str, int] = {}
    for r in records:
        c = concern_for(r)
        counts[c] = counts.get(c, 0) + 1
    return dict(sorted(counts.items()))