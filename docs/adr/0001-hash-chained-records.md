# 0001. Records are hash-chained

**Status:** Accepted

## Context

An evidence ledger's whole value is that its records cannot be altered after the fact without detection. A plain append-only log does not provide this: anyone who can edit the file can change a past record and leave no trace.

## Decision

Each record's hash is computed over the previous record's hash concatenated with this record's canonical body: `record_hash = SHA256(prev_hash + canonical_body)`. The first record chains from a fixed genesis hash. Verification re-walks the chain and, at each record, checks that the stored hash matches the recomputed hash and that the prev_hash matches the prior record.

Canonical serialization (sorted keys, tight separators, UTF-8) makes the hashed bytes deterministic across machines, so the chain is verifiable anywhere.

## Consequences

**Gained:** Altering any record changes its hash, which breaks the link for every record after it. Tampering is detectable, and because a break propagates, the first break is the actionable one -- the verifier reports it by sequence and cause.

**Accepted:** The chain is linear and single-writer; appends are serialized. This is a local-state audit tool, not a distributed ledger, and that is the right scope for recording one agent runtime's actions.
