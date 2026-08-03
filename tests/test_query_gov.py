"""Query, stats, and the governance layer."""

from __future__ import annotations

import pytest

from ledger.governance import concern_coverage, concern_for
from ledger.query import query, stats
from ledger.store import LedgerStore


@pytest.fixture
def records(tmp_path):
    s = LedgerStore(tmp_path / "t.ledger.jsonl")
    s.append("agent-a", "deploy", "svc-x", {})
    s.append("agent-a", "config-change", "svc-x", {})
    s.append("agent-b", "data-export", "cust-db", {})
    return s.read_all()


def test_query_by_actor(records):
    assert len(query(records, actor="agent-a")) == 2


def test_query_by_action(records):
    assert len(query(records, action="data-export")) == 1


def test_query_combined_filters(records):
    assert len(query(records, actor="agent-a", action="deploy")) == 1


def test_stats_counts(records):
    s = stats(records)
    assert s.total_records == 3
    assert s.actors == {"agent-a": 2, "agent-b": 1}
    assert s.integrity_ok


def test_governance_concern_mapping(records):
    assert concern_for(records[2]) == "data_governance"  # data-export


def test_unmapped_action_is_general(tmp_path):
    s = LedgerStore(tmp_path / "t.ledger.jsonl")
    s.append("a", "something-novel", "t", {})
    assert concern_for(s.read_all()[0]) == "general"


def test_concern_coverage(records):
    cov = concern_coverage(records)
    assert cov["deployment_authorization"] == 1
    assert cov["data_governance"] == 1