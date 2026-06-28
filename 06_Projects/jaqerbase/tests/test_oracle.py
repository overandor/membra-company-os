from arrowcap.oracle import run_hidden_tests

HIDDEN_TEST = b'''
import submitted_answer

def test_normal_division():
    assert submitted_answer.safe_divide(10, 2) == 5

def test_divide_by_zero_returns_none():
    assert submitted_answer.safe_divide(10, 0) is None
'''

GOOD_ANSWER = b'''
def safe_divide(a, b):
    if b == 0:
        return None
    return a / b
'''

BROKEN_ANSWER = b'''
def safe_divide(a, b):
    return a / b
'''


def test_oracle_passes_correct_answer(tmp_path):
    hidden = tmp_path / "test_hidden.py"
    hidden.write_bytes(HIDDEN_TEST)
    report = run_hidden_tests(GOOD_ANSWER, str(hidden))
    assert report.passed is True
    assert report.tests_passed == 2
    assert report.tests_failed == 0
    assert report.timed_out is False
    assert report.exit_code == 0


def test_oracle_fails_broken_answer(tmp_path):
    hidden = tmp_path / "test_hidden.py"
    hidden.write_bytes(HIDDEN_TEST)
    report = run_hidden_tests(BROKEN_ANSWER, str(hidden))
    assert report.passed is False
    assert report.tests_failed >= 1
    assert "ZeroDivisionError" in report.stdout_tail


def test_oracle_handles_syntax_error_in_answer(tmp_path):
    hidden = tmp_path / "test_hidden.py"
    hidden.write_bytes(HIDDEN_TEST)
    report = run_hidden_tests(b"def broken(:\n    pass", str(hidden))
    assert report.passed is False


def test_oracle_supports_directory_of_hidden_tests(tmp_path):
    hidden_dir = tmp_path / "hidden"
    hidden_dir.mkdir()
    (hidden_dir / "test_a.py").write_bytes(HIDDEN_TEST)
    report = run_hidden_tests(GOOD_ANSWER, str(hidden_dir))
    assert report.passed is True
    assert report.tests_passed == 2


def test_oracle_times_out_on_infinite_loop(tmp_path):
    hidden = tmp_path / "test_hidden.py"
    hidden.write_bytes(
        b"import submitted_answer\n\ndef test_hang():\n    submitted_answer.hang()\n"
    )
    hanging_answer = b"def hang():\n    while True:\n        pass\n"
    report = run_hidden_tests(hanging_answer, str(hidden), timeout_seconds=2)
    assert report.timed_out is True
    assert report.passed is False
