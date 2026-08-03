# Changelog

## [0.1.0] - 2026-08-03

### Added
- Hash-chained evidence record with canonical, deterministic serialization
- Append-only JSONL store with a self-healing head sidecar (real local state)
- Chain verifier that pinpoints the first broken record and its cause
- Query, stats, and an optional governance-concern annotation layer
- MCP server exposing five tools (append, verify, get, query, stats) over stdio
- CLI for human inspection and verification
- Two runnable demo specs, including live tamper detection
- 27 tests, all offline
