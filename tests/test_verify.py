"""The verifier: the tamper-detection heart of the tool.

These tests simulate real attacks on the ledger file -- alteration, deletion,
reordering, insertion -- and assert the verifier catches each and names the
first broken record.
"""

from __future__ import annotations

import json

import pytest

from ledger.record import Record
from ledger.store import LedgerStore
from ledger.verify import verify_chain


@pytest.fixture
def store(tmp_path):
    s = LedgerStore(tmp_path / "t.ledger.jsonl")
    for i in range(5):
        s.append(f"agent-{i % 2}", "action", f"target-{i}", {"n": i})
    return s


def test_clean_chain_verifies(store):
    result = verify_chain(store.read_all())
    assert result.ok
    assert result.records_checked == 5


def test_empty_chain_is_ok():
    assert verify_chain([]).ok


def test_altered_content_is_detected(store, tmp_path):
    path = tmp_path / "t.ledger.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    rec = json.loads(lines[2])
    rec["details"] = {"n": 999}  # tamper: change payload, keep old hash
    lines[2] = json.dumps(rec, sort_keys=True, separators=(",", ":"))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = verify_chain(store.read_all())
    assert not result.ok
    assert result.break_seq == 2
    assert "content altered" in result.break_reason


def test_removed_record_is_detected(store, tmp_path):
    path = tmp_path / "t.ledger.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    del lines[2]  # remove a record -> seq gap + broken link
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = verify_chain(store.read_all())
    assert not result.ok
    assert result.break_seq == 3  # the record after the hole


def test_reordered_records_detected(store, tmp_path):
    path = tmp_path / "t.ledger.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    lines[1], lines[2] = lines[2], lines[1]  # swap two records
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = verify_chain(store.read_all())
    assert not result.ok


def test_inserted_record_detected(store, tmp_path):
    path = tmp_path / "t.ledger.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    forged = Record.create(2, "attacker", "inject", "t", {}, "0" * 64).to_dict()
    lines.insert(2, json.dumps(forged, sort_keys=True, separators=(",", ":")))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = verify_chain(store.read_all())
    assert not result.ok