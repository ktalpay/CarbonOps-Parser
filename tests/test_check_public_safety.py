from pathlib import Path

from scripts.check_public_safety import (
    format_findings,
    main,
    scan_repository,
)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_clean_text_passes(tmp_path) -> None:
    _write_text(tmp_path / "docs" / "note.md", "Local deterministic note.\n")

    assert scan_repository(tmp_path) == []


def test_restricted_public_claim_is_detected(tmp_path) -> None:
    risky_text = "This tool is " + "production" + "-ready" + ".\n"
    _write_text(tmp_path / "docs" / "claim.md", risky_text)

    findings = scan_repository(tmp_path)

    assert len(findings) == 1
    assert findings[0].category == "public claim risk"
    assert findings[0].path == Path("docs/claim.md")


def test_restricted_visa_wording_is_detected(tmp_path) -> None:
    risky_text = "Avoid " + "Global " + "Talent " + "Visa" + " wording.\n"
    _write_text(tmp_path / "docs" / "wording.md", risky_text)

    findings = scan_repository(tmp_path)

    assert len(findings) == 1
    assert findings[0].category == "restricted wording risk"


def test_sensitive_assignment_wording_is_detected(tmp_path) -> None:
    risky_text = "api_" + "key = value\n"
    _write_text(tmp_path / "config.txt", risky_text)

    findings = scan_repository(tmp_path)

    assert len(findings) == 1
    assert findings[0].category == "sensitive text risk"


def test_remote_reference_is_detected(tmp_path) -> None:
    risky_text = "Remote reference: " + "https" + "://example.invalid/source\n"
    _write_text(tmp_path / "docs" / "remote.md", risky_text)

    findings = scan_repository(tmp_path)

    assert len(findings) == 1
    assert findings[0].category == "remote reference risk"


def test_ignored_directories_are_skipped(tmp_path) -> None:
    risky_text = "This tool is " + "production" + "-ready" + ".\n"
    _write_text(tmp_path / ".git" / "ignored.txt", risky_text)

    assert scan_repository(tmp_path) == []


def test_binary_like_files_are_skipped_safely(tmp_path) -> None:
    risky_bytes = b"\x00" + b"production" + b"-ready"
    path = tmp_path / "binary.dat"
    path.write_bytes(risky_bytes)

    assert scan_repository(tmp_path) == []


def test_output_includes_path_and_line_number(tmp_path) -> None:
    risky_text = "safe\n" + "password" + " = value\n"
    _write_text(tmp_path / "bad.txt", risky_text)

    findings = scan_repository(tmp_path)
    output = format_findings(findings)

    assert "bad.txt:2" in output
    assert "sensitive text risk" in output


def test_cli_returns_nonzero_when_findings_exist(tmp_path, capsys) -> None:
    risky_text = "Visit " + "ftp" + "://example.invalid/source\n"
    _write_text(tmp_path / "bad.txt", risky_text)

    exit_code = main([str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "bad.txt:1" in output


def test_cli_returns_zero_when_clean(tmp_path, capsys) -> None:
    _write_text(tmp_path / "clean.txt", "local fixture only\n")

    exit_code = main([str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Public safety check passed." in output
