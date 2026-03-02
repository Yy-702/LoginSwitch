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


def test_scan_config_candidates_prefers_syclient_properties(tmp_path: Path) -> None:
    exe = tmp_path / "npserver.exe"
    exe.write_text("", encoding="utf-8")
    props = tmp_path / "syclient.properties"
    props.write_text(
        "ip=192.168.9.120:8000\nuserid=200000901\nmac=AA-BB\n",
        encoding="utf-8",
    )

    result = scan_config_candidates(str(exe))
    assert result is not None
    assert result["path"] == str(props)
    assert result["format"] == "properties"


def test_scan_config_candidates_find_syclient_under_conf(tmp_path: Path) -> None:
    exe = tmp_path / "npserver.exe"
    exe.write_text("", encoding="utf-8")
    conf_dir = tmp_path / "conf"
    conf_dir.mkdir()
    props = conf_dir / "syclient.properties"
    props.write_text(
        "ip=192.168.9.120:8000\nuserid=200000901\nmac=AA-BB\n",
        encoding="utf-8",
    )

    result = scan_config_candidates(str(exe))
    assert result is not None
    assert result["path"] == str(props)
    assert result["format"] == "properties"


def test_scan_config_candidates_support_app_path_as_directory(tmp_path: Path) -> None:
    conf_dir = tmp_path / "conf"
    conf_dir.mkdir()
    props = conf_dir / "syclient.properties"
    props.write_text(
        "ip=192.168.9.120:8000\nuserid=200000901\nmac=AA-BB\n",
        encoding="utf-8",
    )

    result = scan_config_candidates(str(tmp_path))
    assert result is not None
    assert result["path"] == str(props)


def test_scan_config_candidates_prefer_conf_over_root_same_name(tmp_path: Path) -> None:
    exe = tmp_path / "npserver.exe"
    exe.write_text("", encoding="utf-8")

    root_props = tmp_path / "syclient.properties"
    root_props.write_text(
        "ip=10.0.0.1:8000\nuserid=root_user\nmac=ROOT\n",
        encoding="utf-8",
    )

    conf_dir = tmp_path / "conf"
    conf_dir.mkdir()
    conf_props = conf_dir / "syclient.properties"
    conf_props.write_text(
        "ip=192.168.9.120:8000\nuserid=200000901\nmac=AA-BB\n",
        encoding="utf-8",
    )

    result = scan_config_candidates(str(exe))
    assert result is not None
    assert result["path"] == str(conf_props)
