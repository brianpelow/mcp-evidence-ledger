"""The append-only store on real (temp) local state."""

from __future__ import annotations

import pytest

from ledger.store import LedgerStore


@pytest.fixture
def store(tmp_path):
    return LedgerStore(tmp_path / "test.ledger.jsonl")


def test_append_returns_chained_records(store):
    r0 = store.append("a", "deploy", "svc", {})
    r1 = store.append("a", "rollback", "svc", {})
    assert r0.seq == 0 and r1.seq == 1
    assert r1.prev_hash == r0.record_hash


def test_persists_across_reopen(store, tmp_path):
    store.append("a", "act", "t", {})
    store.append("a", "act", "t", {})
    reopened = LedgerStore(tmp_path / "test.ledger.jsonl")
    assert len(reopened.read_all()) == 2


def test_head_tracks_tip(store):
    store.append("a", "act", "t", {})
    r1 = store.append("a", "act", "t", {})
    assert store.head().seq == 1
    assert store.head().head_hash == r1.record_hash


def test_head_rebuilds_if_sidecar_deleted(store):
    store.append("a", "act", "t", {})
    r1 = store.append("a", "act", "t", {})
    store._head_path.unlink()  # simulate lost sidecar
    # Reading head should rebuild from the log
    assert store.head().head_hash == r1.record_hash


def test_empty_ledger_reads_empty(store):
    assert store.read_all() == []
    assert store.head().is_empty


def test_get_by_seq(store):
    store.append("a", "first", "t", {})
    store.append("a", "second", "t", {})
    assert store.get(1).action == "second"
    assert store.get(99) is None


def test_the_raw_file_is_human_readable_jsonl(store, tmp_path):
    store.append("agent-a", "deploy", "svc-x", {"env": "prod"})
    text = (tmp_path / "test.ledger.jsonl").read_text(encoding="utf-8")
    assert '"action":"deploy"' in text
    assert text.count("\n") == 1  # one record, one line