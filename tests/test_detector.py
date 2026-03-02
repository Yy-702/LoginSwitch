from pathlib import Path

from loginswitch.adapters.detector import (
    detect_adapter_mode,
    detect_with_probe,
    scan_config_candidates,
)


def test_detecter_prefers_config_file() -> None:
    mode = detect_adapter_mode(config_file_hit=True, registry_hit=True)
    assert mode == "config_file"


def test_detecter_fallback_to_registry() -> None:
    mode = detect_adapter_mode(config_file_hit=False, registry_hit=True)
    assert mode == "registry"


def test_detecter_fallback_to_ui_automation() -> None:
    mode = detect_adapter_mode(config_file_hit=False, registry_hit=False)
    assert mode == "ui_automation"


def test_scan_config_candidates_skip_unrelated_file(tmp_path: Path) -> None:
    exe = tmp_path / "client.exe"
    exe.write_text("", encoding="utf-8")
    (tmp_path / "random.ini").write_text("[General]\nfoo=bar\n", encoding="utf-8")

    result = scan_config_candidates(str(exe))
    assert result is None


def test_scan_config_candidates_match_login_file(tmp_path: Path) -> None:
    exe = tmp_path / "client.exe"
    exe.write_text("", encoding="utf-8")
    ini = tmp_path / "client.ini"
    ini.write_text(
        "[Login]\nserver=192.168.1.1:8000\nuser_id=qa01\n",
        encoding="utf-8",
    )

    result = scan_config_candidates(str(exe))
    assert result is not None
    assert result["path"] == str(ini)


def test_detect_with_probe_uses_ui_automation_defaults(tmp_path: Path) -> None:
    exe = tmp_path / "client.exe"
    mode, config = detect_with_probe(str(exe))
    assert mode == "ui_automation"
    assert "window_title_re" in config
    assert "window_class_re" in config
    assert "wait_timeout_sec" in config
