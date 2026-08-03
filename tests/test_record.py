"""The chain core: deterministic hashing and tamper-evident recomputation."""

from __future__ import annotations

from ledger.record import GENESIS_HASH, Record


def test_hash_is_deterministic():
    a = Record.create(0, "x", "act", "t", {"k": 1}, GENESIS_HASH, timestamp="2026-01-01T00:00:00+00:00")
    b = Record.create(0, "x", "act", "t", {"k": 1}, GENESIS_HASH, timestamp="2026-01-01T00:00:00+00:00")
    assert a.record_hash == b.record_hash


def test_hash_changes_with_content():
    a = Record.create(0, "x", "act", "t", {"k": 1}, GENESIS_HASH, timestamp="2026-01-01T00:00:00+00:00")
    b = Record.create(0, "x", "act", "t", {"k": 2}, GENESIS_HASH, timestamp="2026-01-01T00:00:00+00:00")
    assert a.record_hash != b.record_hash


def test_chain_links_via_prev_hash():
    a = Record.create(0, "x", "act", "t", {}, GENESIS_HASH, timestamp="2026-01-01T00:00:00+00:00")
    b = Record.create(1, "x", "act", "t", {}, a.record_hash, timestamp="2026-01-01T00:00:01+00:00")
    assert b.prev_hash == a.record_hash


def test_recompute_matches_for_untouched_record():
    a = Record.create(0, "x", "act", "t", {"k": 1}, GENESIS_HASH)
    assert a.recompute_hash() == a.record_hash


def test_recompute_detects_alteration():
    a = Record.create(0, "x", "act", "t", {"k": 1}, GENESIS_HASH)
    # Forge a record with altered details but the original hash
    forged = Record(a.seq, a.timestamp, a.actor, a.action, a.target, {"k": 999}, a.prev_hash, a.record_hash)
    assert forged.recompute_hash() != forged.record_hash


def test_roundtrip_dict():
    a = Record.create(0, "x", "act", "t", {"k": 1}, GENESIS_HASH)
    assert Record.from_dict(a.to_dict()) == a


def test_first_record_chains_from_genesis():
    a = Record.create(0, "x", "act", "t", {}, GENESIS_HASH)
    assert a.prev_hash == GENESIS_HASH