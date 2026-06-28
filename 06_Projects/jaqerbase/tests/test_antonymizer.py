from arrowcap.antonymizer import antonymify, length_bucket, verify_binding
from arrowcap.commitment import sha256_hex


def test_length_bucket_boundaries():
    assert length_bucket(0) == "empty"
    assert length_bucket(1) == "tiny"
    assert length_bucket(255) == "tiny"
    assert length_bucket(256) == "small"
    assert length_bucket(4095) == "small"
    assert length_bucket(4096) == "medium"
    assert length_bucket(65535) == "medium"
    assert length_bucket(65536) == "large"
    assert length_bucket((1 << 20) - 1) == "large"
    assert length_bucket(1 << 20) == "huge"


def test_antonymify_never_leaks_content_but_binds_commitment():
    content = b"def add(a, b):\n    return a + b\n"
    profile = antonymify(content, "source")
    assert profile.commitment_sha256 == sha256_hex(content)
    serialized = str(profile.to_dict())
    assert "return a + b" not in serialized


def test_antonymify_flags_risky_predicates_and_scores_risk():
    risky = b"import subprocess\ndef run(cmd):\n    eval(cmd)\n    subprocess.run(cmd)\n"
    profile = antonymify(risky, "source")
    assert "uses_eval_or_exec" in profile.affirmed
    assert "uses_subprocess_or_shell" in profile.affirmed
    assert profile.risk_score > 0.5
    assert "does_not_uses_network_io" in profile.negated


def test_antonymify_clean_code_has_zero_risk():
    clean = b"def add(a, b):\n    return a + b\n"
    profile = antonymify(clean, "source")
    assert profile.risk_score == 0.0
    assert "does_not_uses_eval_or_exec" in profile.negated


def test_antonymify_generic_text_uses_generic_predicates_only():
    profile = antonymify(b"contact me at someone@example.com", "text")
    assert "contains_email_like" in profile.affirmed
    assert "uses_eval_or_exec" not in profile.affirmed
    assert "does_not_uses_eval_or_exec" not in profile.negated


def test_antonymify_to_dict_sorts_and_counts_negations():
    profile = antonymify(b"plain text", "text")
    d = profile.to_dict()
    assert d["affirmed"] == sorted(d["affirmed"])
    assert d["negated"] == sorted(d["negated"])
    assert d["exclusion_count"] == len(profile.negated)


def test_antonymify_round_trips_through_dict():
    from arrowcap.antonymizer import AntonymProfile

    profile = antonymify(b"hello world\nsecond line", "text")
    restored = AntonymProfile.from_dict(profile.to_dict())
    assert restored.commitment_sha256 == profile.commitment_sha256
    assert set(restored.affirmed) == set(profile.affirmed)
    assert set(restored.negated) == set(profile.negated)


def test_verify_binding_passes_for_identical_content():
    content = b"def safe(): return True\n"
    profile = antonymify(content, "source")
    ok, mismatches = verify_binding(profile, content)
    assert ok is True
    assert mismatches == []


def test_verify_binding_fails_for_tampered_content():
    original = b"def safe(): return True\n"
    profile = antonymify(original, "source")
    tampered = b"import os\ndef safe(): os.system('echo hi'); return True\n"
    ok, mismatches = verify_binding(profile, tampered)
    assert ok is False
    assert "sha256_mismatch" in mismatches
    assert "affirmed_predicate_mismatch" in mismatches


def test_verify_binding_detects_length_bucket_drift():
    original = b"x" * 50
    profile = antonymify(original, "text")
    much_longer = b"y" * 5000
    ok, mismatches = verify_binding(profile, much_longer)
    assert ok is False
    assert "length_bucket_mismatch" in mismatches
