"""The MCP server: five tools exposing the evidence ledger to an agent.

The tools are deliberately shaped around the integrity guarantee:

- append_record   -- write an evidence entry, receive a tamper-evident receipt
- verify_ledger   -- re-walk the chain, prove integrity or pinpoint the break
- get_record      -- fetch one record by sequence
- query_ledger    -- filter records by actor / action / target / time
- ledger_stats    -- counts, head hash, and a live integrity check

There is deliberately NO update tool and NO delete tool. Append-only is the
guarantee; exposing mutation would defeat it. An agent can write history and
read history, but never rewrite it.

The ledger path comes from the EVIDENCE_LEDGER_PATH environment variable so an
operator controls where evidence lands, not the calling agent. Defaults to
./evidence.ledger.jsonl.

This module imports the MCP SDK lazily so the rest of the package (and its
tests) work without the optional `mcp` extra installed.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from ledger.governance import concern_for
from ledger.query import query, stats
from ledger.store import LedgerStore
from ledger.verify import verify_chain


def _ledger_path() -> Path:
    return Path(os.environ.get("EVIDENCE_LEDGER_PATH", "evidence.ledger.jsonl"))


def _store() -> LedgerStore:
    return LedgerStore(_ledger_path())


# --- tool implementations (pure-ish; return JSON-serializable dicts) --------
# These are separated from the MCP wiring so they are unit-testable without the
# MCP runtime.

def tool_append_record(actor: str, action: str, target: str,
                       details: dict | None = None) -> dict:
    store = _store()
    rec = store.append(actor, action, target, details or {})
    return {
        "receipt": {
            "seq": rec.seq,
            "record_hash": rec.record_hash,
            "prev_hash": rec.prev_hash,
            "timestamp": rec.timestamp,
        },
        "governance_concern": concern_for(rec),
        "message": f"Evidence recorded at seq {rec.seq}. Receipt hash {rec.record_hash[:16]}...",
    }


def tool_verify_ledger() -> dict:
    result = verify_chain(_store().read_all())
    return {**result.to_dict(), "summary": result.summary()}


def tool_get_record(seq: int) -> dict:
    rec = _store().get(seq)
    if rec is None:
        return {"found": False, "seq": seq}
    return {"found": True, "record": rec.to_dict(), "governance_concern": concern_for(rec)}


def tool_query_ledger(actor: str | None = None, action: str | None = None,
                      target: str | None = None, since: str | None = None,
                      until: str | None = None) -> dict:
    recs = query(_store().read_all(), actor=actor, action=action,
                 target=target, since=since, until=until)
    return {"count": len(recs), "records": [r.to_dict() for r in recs]}


def tool_ledger_stats() -> dict:
    return stats(_store().read_all()).to_dict()


# --- MCP wiring -------------------------------------------------------------

def build_server():
    """Construct the MCP server. Imports the SDK lazily."""
    from mcp.server import Server
    from mcp.types import TextContent, Tool

    server = Server("evidence-ledger")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="append_record",
                description=(
                    "Record an evidence entry for an agent action and receive a "
                    "tamper-evident receipt (a hash chained to all prior records). "
                    "Use before or after any consequential action."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "actor": {"type": "string", "description": "The agent or identity taking the action."},
                        "action": {"type": "string", "description": "The action taken, e.g. deploy, config-change, data-export."},
                        "target": {"type": "string", "description": "What the action was performed on."},
                        "details": {"type": "object", "description": "Any additional structured context."},
                    },
                    "required": ["actor", "action", "target"],
                },
            ),
            Tool(
                name="verify_ledger",
                description=(
                    "Re-walk the entire hash chain and prove integrity, or pinpoint "
                    "the exact record where tampering occurred. Run this to trust the trail."
                ),
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="get_record",
                description="Fetch a single evidence record by its sequence number.",
                inputSchema={
                    "type": "object",
                    "properties": {"seq": {"type": "integer"}},
                    "required": ["seq"],
                },
            ),
            Tool(
                name="query_ledger",
                description="Filter evidence records by actor, action, target, and/or time range.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "actor": {"type": "string"},
                        "action": {"type": "string"},
                        "target": {"type": "string"},
                        "since": {"type": "string", "description": "ISO timestamp lower bound."},
                        "until": {"type": "string", "description": "ISO timestamp upper bound."},
                    },
                },
            ),
            Tool(
                name="ledger_stats",
                description="Summary of the ledger: record counts by actor and action, head hash, and a live integrity check.",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list:
        dispatch = {
            "append_record": lambda a: tool_append_record(
                a["actor"], a["action"], a["target"], a.get("details")),
            "verify_ledger": lambda a: tool_verify_ledger(),
            "get_record": lambda a: tool_get_record(a["seq"]),
            "query_ledger": lambda a: tool_query_ledger(
                a.get("actor"), a.get("action"), a.get("target"),
                a.get("since"), a.get("until")),
            "ledger_stats": lambda a: tool_ledger_stats(),
        }
        handler = dispatch.get(name)
        if handler is None:
            result = {"error": f"unknown tool: {name}"}
        else:
            result = handler(arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    return server


def main() -> None:
    """Run the server over stdio."""
    import asyncio

    from mcp.server.stdio import stdio_server

    async def _run():
        server = build_server()
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()