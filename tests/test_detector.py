from loginswitch.adapters.detector import detect_adapter_mode


def test_detecter_prefers_config_file() -> None:
    mode = detect_adapter_mode(config_file_hit=True, registry_hit=True)
    assert mode == "config_file"


def test_detecter_fallback_to_registry() -> None:
    mode = detect_adapter_mode(config_file_hit=False, registry_hit=True)
    assert mode == "registry"


def test_detecter_fallback_to_ui_automation() -> None:
    mode = detect_adapter_mode(config_file_hit=False, registry_hit=False)
    assert mode == "ui_automation"
