import json
import os
import time

import pytest

from chronoswarm.cli import main
from chronoswarm.tmuxctl import TmuxController


def unique_session_name(prefix: str = "cs-cli") -> str:
    return f"{prefix}-{os.getpid()}-{int(time.time() * 1_000_000)}"


@pytest.fixture
def cli_session():
    session_name = unique_session_name("cs-cli")
    yield session_name
    TmuxController(session_name).kill_session()


def _run(capsys, argv):
    exit_code = main(argv)
    captured = capsys.readouterr()
    return exit_code, captured.out, captured.err


def test_start_session_outputs_pane_id(tmp_path, cli_session, capsys):
    data_dir = str(tmp_path)
    code, out, err = _run(
        capsys, ["--data-dir", data_dir, "--session", cli_session, "start-session"]
    )
    assert code == 0
    payload = json.loads(out)
    assert payload["pane_id"] == "%0"
    assert payload["session_name"] == cli_session


def test_split_outputs_new_pane(tmp_path, cli_session, capsys):
    data_dir = str(tmp_path)
    _run(capsys, ["--data-dir", data_dir, "--session", cli_session, "start-session"])
    code, out, err = _run(
        capsys, ["--data-dir", data_dir, "--session", cli_session, "split", "--pane-id", "%0"]
    )
    assert code == 0
    payload = json.loads(out)
    assert payload["pane_id"] == "%1"


def test_list_panes_outputs_array_with_both_panes(tmp_path, cli_session, capsys):
    data_dir = str(tmp_path)
    _run(capsys, ["--data-dir", data_dir, "--session", cli_session, "start-session"])
    _run(capsys, ["--data-dir", data_dir, "--session", cli_session, "split", "--pane-id", "%0"])
    code, out, err = _run(capsys, ["--data-dir", data_dir, "--session", cli_session, "list-panes"])
    assert code == 0
    payload = json.loads(out)
    assert len(payload) == 2


def test_send_keys_touches_activity(tmp_path, cli_session, capsys):
    data_dir = str(tmp_path)
    _run(capsys, ["--data-dir", data_dir, "--session", cli_session, "start-session"])
    code, out, err = _run(
        capsys,
        ["--data-dir", data_dir, "--session", cli_session, "send-keys", "--pane-id", "%0", "--keys", "echo hi"],
    )
    assert code == 0
    payload = json.loads(out)
    assert payload["sent"] == "echo hi"
    assert payload["activity_ts"] > 0


def test_breed_outputs_applied_result(tmp_path, cli_session, capsys):
    data_dir = str(tmp_path)
    _run(capsys, ["--data-dir", data_dir, "--session", cli_session, "start-session"])
    _run(capsys, ["--data-dir", data_dir, "--session", cli_session, "split", "--pane-id", "%0"])
    code, out, err = _run(
        capsys,
        ["--data-dir", data_dir, "--session", cli_session, "breed", "--generations", "5", "--population", "8", "--seed", "3"],
    )
    assert code == 0
    payload = json.loads(out)
    assert payload["applied"] is True
    assert payload["pane_count"] == 2


def test_tick_outputs_list(tmp_path, cli_session, capsys):
    data_dir = str(tmp_path)
    _run(capsys, ["--data-dir", data_dir, "--session", cli_session, "start-session"])
    code, out, err = _run(capsys, ["--data-dir", data_dir, "--session", cli_session, "tick"])
    assert code == 0
    payload = json.loads(out)
    assert isinstance(payload, list)


def test_status_unknown_pane_returns_error_exit_code(tmp_path, cli_session, capsys):
    data_dir = str(tmp_path)
    _run(capsys, ["--data-dir", data_dir, "--session", cli_session, "start-session"])
    code, out, err = _run(
        capsys, ["--data-dir", data_dir, "--session", cli_session, "status", "--pane-id", "%999"]
    )
    assert code == 1
    assert "no such pane" in err


def test_status_known_pane_outputs_record(tmp_path, cli_session, capsys):
    data_dir = str(tmp_path)
    _run(capsys, ["--data-dir", data_dir, "--session", cli_session, "start-session"])
    code, out, err = _run(
        capsys, ["--data-dir", data_dir, "--session", cli_session, "status", "--pane-id", "%0"]
    )
    assert code == 0
    payload = json.loads(out)
    assert payload["pane_id"] == "%0"


def test_receipts_outputs_array(tmp_path, cli_session, capsys):
    data_dir = str(tmp_path)
    _run(capsys, ["--data-dir", data_dir, "--session", cli_session, "start-session"])
    _run(capsys, ["--data-dir", data_dir, "--session", cli_session, "split", "--pane-id", "%0"])
    _run(capsys, ["--data-dir", data_dir, "--session", cli_session, "breed", "--seed", "1"])
    code, out, err = _run(capsys, ["--data-dir", data_dir, "--session", cli_session, "receipts"])
    assert code == 0
    payload = json.loads(out)
    assert len(payload) == 2


def test_kill_session_outputs_killed_and_session_gone(tmp_path, cli_session, capsys):
    data_dir = str(tmp_path)
    _run(capsys, ["--data-dir", data_dir, "--session", cli_session, "start-session"])
    code, out, err = _run(capsys, ["--data-dir", data_dir, "--session", cli_session, "kill-session"])
    assert code == 0
    payload = json.loads(out)
    assert payload["killed"] == cli_session
    assert TmuxController(cli_session).session_exists() is False


def test_send_keys_to_unknown_pane_is_protocol_error(tmp_path, cli_session, capsys):
    data_dir = str(tmp_path)
    _run(capsys, ["--data-dir", data_dir, "--session", cli_session, "start-session"])
    code, out, err = _run(
        capsys,
        ["--data-dir", data_dir, "--session", cli_session, "send-keys", "--pane-id", "%999", "--keys", "echo hi"],
    )
    assert code == 1
    assert err.strip() != ""
