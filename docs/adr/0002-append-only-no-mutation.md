# 0002. The ledger is append-only; no update or delete tool exists

**Status:** Accepted

## Context

It is tempting to offer a "correct a record" or "redact a record" tool for convenience. Any such tool would destroy the guarantee the ledger exists to provide.

## Decision

The MCP surface exposes append, read, verify, query, and stats. It exposes no update and no delete. The store class has no mutation method. Correcting the record of history is done by appending a new record that references the correction, never by altering the past.

## Consequences

**Gained:** The integrity guarantee is structural, not merely promised. There is no code path through the server that can rewrite a past record, so an agent (or a bug) cannot erase evidence.

**Accepted:** A genuine mistake in a recorded entry stays in the ledger, corrected by a later appended entry rather than erased. That is the correct behavior for an audit trail: the mistake and its correction are both part of the true history.

**Detected:** Editing the underlying file directly, outside the server, is still physically possible -- and is exactly what `verify` catches. The demo in `specs/demo_tamper.py` proves it.
