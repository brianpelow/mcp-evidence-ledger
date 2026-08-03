# Contributing

## Setup

```bash
uv sync --all-extras
uv run pytest
uv run ruff check src tests
```

## The invariants

1. **The chain stays deterministic.** Canonical serialization only; no wall-clock or ordering dependence in the hashed body beyond the recorded timestamp. Same records in, same chain out.
2. **Append-only stays absolute.** Do not add an update or delete path anywhere. Corrections are new appended records. See ADR 0002.
3. **No LLM in the ledger.** Hashing, chaining, verification, and querying are pure and deterministic.

## Tests make no network calls

Everything runs on temp-file local state. The MCP tool implementations are separated from the MCP runtime so they are unit-testable directly.
