# mcp-evidence-ledger

> An MCP server providing an append-only, hash-chained evidence ledger for agent actions. Every record is a tamper-evident receipt cryptographically bound to all prior records, persisted as human-readable local state. Deterministic, no LLM. **Agents are non-deterministic; their audit trail should not be.**

![CI](https://github.com/brianpelow/mcp-evidence-ledger/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)

## The idea

When an autonomous agent acts, you need a record of what it did that cannot be quietly altered afterward. This is that record: an append-only ledger where each entry's hash is computed over the previous entry's hash, forming a chain. Altering any past record breaks every hash after it, so tampering is not just discouraged -- it is detectable, and the exact altered record can be named.

It runs as an MCP server, so any agent can call it as a tool. The evidence lands in a plain JSONL file you can open and read: a complete, ordered, cryptographically linked account of every action.

## Why it is built this way

**Hash-chained, like a mini ledger.** `record_hash = SHA256(prev_hash + canonical_body)`. The chain is the integrity guarantee. See ADR 0001.

**Append-only, enforced by absence.** The server exposes append, read, verify -- and deliberately no update and no delete. History can be written and read, never rewritten. See ADR 0002.

**Real, human-readable local state.** The ledger is JSONL, one record per line, chosen over a binary store so you can `cat` your own audit trail. If someone edits the file directly, `verify` catches it -- which is the point.

**Deterministic. No LLM anywhere.** Hashing, chaining, and verification are pure functions of the records. Nothing here is probabilistic. An evidence ledger that could be talked out of a finding would not be evidence.

## Prove it yourself

Two runnable demos write real ledgers you can inspect:

```bash
uv run python specs/demo_basic.py    # record agent actions, verify the chain
uv run python specs/demo_tamper.py   # edit a record in the file, watch verify catch it
```

`demo_tamper.py` writes a clean ledger, changes an access level from `read` to `admin` directly in the file, and shows the verifier pinpointing the tampered record. Tamper-evidence, demonstrated rather than asserted.

## Run as an MCP server

```bash
uv sync --extra mcp
EVIDENCE_LEDGER_PATH=./evidence.ledger.jsonl uv run python -m ledger.server
```

The operator sets the ledger path via `EVIDENCE_LEDGER_PATH`, not the calling agent -- the agent writes evidence, it does not choose where evidence lands.

### MCP tools

| Tool | What it does |
|------|--------------|
| `append_record` | Record an action, receive a tamper-evident receipt hash |
| `verify_ledger` | Re-walk the chain; prove integrity or pinpoint the first break |
| `get_record` | Fetch one record by sequence |
| `query_ledger` | Filter by actor, action, target, or time range |
| `ledger_stats` | Counts, head hash, and a live integrity check |

There is no update tool and no delete tool. That is deliberate.

## CLI (for humans)

```bash
uv run evidence-ledger --path ./evidence.ledger.jsonl append deploy-agent deploy payments-api --details '{"version":"4.2.0"}'
uv run evidence-ledger --path ./evidence.ledger.jsonl verify
uv run evidence-ledger --path ./evidence.ledger.jsonl stats
```

## What a record contains

The agent supplies the semantics (`actor`, `action`, `target`, `details`). The ledger owns the integrity fields (`seq`, `timestamp`, `prev_hash`, `record_hash`) -- an agent cannot forge a hash or a sequence number, because it never computes them.

## Optional: a governance lens

The core is generic -- any actor, any action. An optional layer maps actions onto the governance failure taxonomy shared across the portfolio (deployment authorization, change management, data governance, and so on), so an evidence ledger can be read through a governance lens without the core depending on it.

## Related work

| Repo | Relationship |
|------|-------------|
| [mcp-governance-gateway](https://github.com/brianpelow/mcp-governance-gateway) | Enforces governance on the write path; this records tamper-evident proof of what happened |
| [ai-governance-framework](https://github.com/brianpelow/ai-governance-framework) | The replay imperative this ledger operationalizes |

## Design decisions

- [0001](./docs/adr/0001-hash-chained-records.md) -- Records are hash-chained
- [0002](./docs/adr/0002-append-only-no-mutation.md) -- The ledger is append-only; no update or delete tool exists

## License

Apache 2.0
