import json
import os

import pytest

from arrowcap import cli as cli_module

HIDDEN_TEST = b'''
import submitted_answer

def test_add():
    assert submitted_answer.add(2, 3) == 5
'''
GOOD_ANSWER = b"def add(a, b):\n    return a + b\n"


@pytest.fixture
def data_dir(tmp_path):
    return str(tmp_path / ".jaqerbase")


@pytest.fixture
def hidden_test_file(tmp_path):
    path = tmp_path / "test_hidden.py"
    path.write_bytes(HIDDEN_TEST)
    return str(path)


@pytest.fixture
def answer_file(tmp_path):
    path = tmp_path / "answer.py"
    path.write_bytes(GOOD_ANSWER)
    return str(path)


def _run(data_dir, args, capsys):
    rc = cli_module.main(["--data-dir", data_dir] + args)
    captured = capsys.readouterr()
    return rc, captured.out, captured.err


def _post_full_claim(
    data_dir, hidden_test_file, answer_file, capsys, *,
    buyer="alice", seller="bob", reward_cents=5000, bond_cents=1000,
):
    rc, out, _ = _run(data_dir, [
        "post-claim", "--buyer", buyer, "--title", "t", "--description", "d",
        "--reward-cents", str(reward_cents), "--hidden-test-path", hidden_test_file,
        "--fund-buyer-cents", "100000",
    ], capsys)
    assert rc == 0
    claim_id = json.loads(out)["claim_id"]

    rc, _, _ = _run(data_dir, [
        "submit-preview", "--claim-id", claim_id, "--seller", seller,
        "--answer-file", answer_file, "--bond-cents", str(bond_cents),
        "--fund-seller-cents", "100000",
    ], capsys)
    assert rc == 0

    rc, out, _ = _run(data_dir, ["status", "--claim-id", claim_id], capsys)
    assert rc == 0
    answer_id = json.loads(out)["answers"][0]["answer_id"]

    assert _run(data_dir, ["post-bond", "--answer-id", answer_id], capsys)[0] == 0
    assert _run(data_dir, ["escrow-pay", "--answer-id", answer_id], capsys)[0] == 0

    rc, out, _ = _run(
        data_dir, ["reveal-answer", "--answer-id", answer_id, "--answer-file", answer_file], capsys
    )
    assert rc == 0
    assert json.loads(out)["binding_ok"] is True

    return claim_id, answer_id


def test_full_cli_lifecycle_settles_and_signs_receipt(data_dir, hidden_test_file, answer_file, capsys):
    _claim_id, answer_id = _post_full_claim(data_dir, hidden_test_file, answer_file, capsys)

    rc, out, _ = _run(data_dir, ["settle", "--answer-id", answer_id, "--sign"], capsys)
    assert rc == 0
    assert '"passed": true' in out

    receipt_path = os.path.join(data_dir, "receipts", f"{answer_id}.json")
    assert os.path.exists(receipt_path)
    with open(receipt_path) as fh:
        receipt = json.load(fh)
    assert receipt["answer_id"] == answer_id
    assert receipt["scheme"] == "ed25519"

    rc, out, _ = _run(data_dir, ["status", "--answer-id", answer_id], capsys)
    assert rc == 0
    assert json.loads(out)["status"] == "settled"


def test_cli_surfaces_protocol_violation_as_nonzero_exit(data_dir, hidden_test_file, answer_file, capsys):
    rc, out, _ = _run(data_dir, [
        "post-claim", "--buyer", "alice", "--title", "t", "--description", "d",
        "--reward-cents", "2000", "--hidden-test-path", hidden_test_file,
        "--fund-buyer-cents", "100000",
    ], capsys)
    claim_id = json.loads(out)["claim_id"]

    _run(data_dir, [
        "submit-preview", "--claim-id", claim_id, "--seller", "bob",
        "--answer-file", answer_file, "--bond-cents", "500",
        "--fund-seller-cents", "100000",
    ], capsys)
    rc, out, _ = _run(data_dir, ["status", "--claim-id", claim_id], capsys)
    answer_id = json.loads(out)["answers"][0]["answer_id"]

    rc, _, err = _run(data_dir, ["escrow-pay", "--answer-id", answer_id], capsys)
    assert rc == 1
    assert "no oracle without a bond" in err


def test_cli_binding_violation_path(data_dir, hidden_test_file, tmp_path, capsys):
    answer_path = tmp_path / "good.py"
    answer_path.write_bytes(GOOD_ANSWER)

    rc, out, _ = _run(data_dir, [
        "post-claim", "--buyer", "alice", "--title", "t", "--description", "d",
        "--reward-cents", "2000", "--hidden-test-path", hidden_test_file,
        "--fund-buyer-cents", "100000",
    ], capsys)
    claim_id = json.loads(out)["claim_id"]

    _run(data_dir, [
        "submit-preview", "--claim-id", claim_id, "--seller", "bob",
        "--answer-file", str(answer_path), "--bond-cents", "500",
        "--fund-seller-cents", "100000",
    ], capsys)
    rc, out, _ = _run(data_dir, ["status", "--claim-id", claim_id], capsys)
    answer_id = json.loads(out)["answers"][0]["answer_id"]

    _run(data_dir, ["post-bond", "--answer-id", answer_id], capsys)
    _run(data_dir, ["escrow-pay", "--answer-id", answer_id], capsys)

    tampered_path = tmp_path / "tampered.py"
    tampered_path.write_bytes(b"import os\n" + GOOD_ANSWER)
    rc, out, err = _run(
        data_dir, ["reveal-answer", "--answer-id", answer_id, "--answer-file", str(tampered_path)], capsys
    )
    assert json.loads(out)["binding_ok"] is False
    assert "binding violation" in err

    rc, out, _ = _run(data_dir, ["settle", "--answer-id", answer_id, "--binding-violation"], capsys)
    assert rc == 0
    assert '"binding_violation": true' in out
    assert '"passed": false' in out


def test_cli_optimize_bonds_uses_real_settlement_history(data_dir, hidden_test_file, answer_file, capsys):
    _claim_id, answer_id = _post_full_claim(data_dir, hidden_test_file, answer_file, capsys)
    rc, _, _ = _run(data_dir, ["settle", "--answer-id", answer_id], capsys)
    assert rc == 0

    rc, out, _ = _run(data_dir, ["optimize-bonds"], capsys)
    assert rc == 0
    assert '"history_size": 1' in out
    assert "recommended bond fraction by risk bucket" in out


def test_cli_status_with_no_claims_returns_empty_list(data_dir, capsys):
    rc, out, _ = _run(data_dir, ["status"], capsys)
    assert rc == 0
    assert json.loads(out) == []
