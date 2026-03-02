from __future__ import annotations

from pathlib import Path


def detect_adapter_mode(config_file_hit: bool, registry_hit: bool) -> str:
    if config_file_hit:
        return "config_file"
    if registry_hit:
        return "registry"
    return "ui_automation"


def scan_config_candidates(app_path: str) -> dict[str, str] | None:
    exe_path = Path(app_path)
    candidates: list[Path] = []

    if exe_path.exists():
        parent = exe_path.parent
        candidates.extend(parent.glob("*.ini"))
        candidates.extend(parent.glob("*.config"))
        candidates.extend(parent.glob("*.xml"))
        candidates.extend(parent.glob("*.json"))

    # 选择第一个可写候选作为配置文件适配目标。
    for candidate in candidates:
        if candidate.is_file():
            return {"path": str(candidate), "section": "Login"}
    return None


def try_registry_probe() -> dict[str, str] | None:
    # 非 Windows 环境无法可靠探测注册表，先返回空。
    return None


def detect_with_probe(app_path: str) -> tuple[str, dict]:
    config = scan_config_candidates(app_path)
    if config:
        return "config_file", config

    reg = try_registry_probe()
    if reg:
        return "registry", reg

    return "ui_automation", {}
