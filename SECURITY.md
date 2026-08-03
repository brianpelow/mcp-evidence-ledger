# Security Policy

## Reporting

Open a [security advisory](https://github.com/brianpelow/mcp-evidence-ledger/security/advisories/new) rather than a public issue.

## Threat model

This tool makes tampering with a past record *detectable*, not *impossible*. Anyone with write access to the ledger file can edit it; the guarantee is that `verify` will catch the edit and name the record. For stronger guarantees, place the ledger on append-only or write-once storage and run `verify` on an independent host.

The ledger path is set by the operator via `EVIDENCE_LEDGER_PATH`, never by the calling agent, so an agent cannot redirect its own evidence.

## No secrets, no network

The server makes no outbound network calls and reads no credentials. It operates only on the local ledger file.
