from __future__ import annotations

import configparser
from pathlib import Path

LOGIN_KEYWORDS = (
    "server",
    "服务器",
    "user",
    "userid",
    "user_id",
    "账号",
    "role",
    "角色",
    "nic",
    "网卡",
    "password",
    "pwd",
)


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
        stem = exe_path.stem.lower()
        preferred_names = (
            f"{stem}.ini",
            f"{stem}.config",
            "config.ini",
            "login.ini",
        )
        for name in preferred_names:
            candidate = parent / name
            if candidate.exists():
                candidates.append(candidate)

        for suffix in ("*.ini", "*.config", "*.xml", "*.json"):
            candidates.extend(parent.glob(suffix))

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.is_file() and _looks_like_login_config(candidate):
            return {"path": str(candidate), "section": _guess_ini_section(candidate)}
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


def _looks_like_login_config(path: Path) -> bool:
    if path.suffix.lower() == ".ini":
        parser = configparser.ConfigParser()
        try:
            parser.read(path, encoding="utf-8")
        except (configparser.Error, OSError):
            return False
        for section in parser.sections():
            keys = [key.lower() for key in parser.options(section)]
            if any(any(keyword in key for keyword in LOGIN_KEYWORDS) for key in keys):
                return True
        return False

    try:
        content = path.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return False
    return any(keyword in content for keyword in LOGIN_KEYWORDS)


def _guess_ini_section(path: Path) -> str:
    if path.suffix.lower() != ".ini":
        return "Login"

    parser = configparser.ConfigParser()
    try:
        parser.read(path, encoding="utf-8")
    except (configparser.Error, OSError):
        return "Login"

    for section in parser.sections():
        section_keys = [key.lower() for key in parser.options(section)]
        if any(key in ("server", "user", "user_id", "userid", "password") for key in section_keys):
            return section
    return "Login"
