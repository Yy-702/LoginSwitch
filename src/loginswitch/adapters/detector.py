from __future__ import annotations

import configparser
import re
from pathlib import Path

LOGIN_KEYWORDS = {
    "server",
    "ip",
    "userid",
    "user_id",
    "user",
    "role",
    "nic",
    "mac",
    "password",
    "pwd",
}


def detect_adapter_mode(config_file_hit: bool, registry_hit: bool) -> str:
    if config_file_hit:
        return "config_file"
    if registry_hit:
        return "registry"
    return "ui_automation"


def scan_config_candidates(app_path: str) -> dict[str, str] | None:
    raw_path = Path(app_path)
    candidates: list[Path] = []

    if raw_path.exists():
        base_dir = raw_path if raw_path.is_dir() else raw_path.parent
        stem = raw_path.stem.lower() if raw_path.is_file() else raw_path.name.lower()

        conf_props = _first_existing(
            base_dir / "conf" / "sysclient.properties",
            base_dir / "conf" / "syclient.properties",
        )
        if conf_props is not None and conf_props.is_file():
            return {
                "path": str(conf_props),
                "format": "properties",
                "keyMap": {"server": "ip", "userId": "userid", "nic": "mac"},
            }

        candidate_dirs = [base_dir / "conf", base_dir / "config", base_dir]
        preferred_names = (
            "sysclient.properties",
            "syclient.properties",
            f"{stem}.ini",
            f"{stem}.config",
            "config.ini",
            "login.ini",
        )

        for directory in candidate_dirs:
            if not directory.exists() or not directory.is_dir():
                continue
            for name in preferred_names:
                candidate = directory / name
                if candidate.exists():
                    candidates.append(candidate)
            for suffix in ("*.properties", "*.ini", "*.config", "*.xml", "*.json"):
                candidates.extend(directory.glob(suffix))

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.name.lower().startswith("log4j"):
            continue
        if candidate.is_file() and _looks_like_login_config(candidate):
            if candidate.suffix.lower() == ".properties":
                return {
                    "path": str(candidate),
                    "format": "properties",
                    "keyMap": {"server": "ip", "userId": "userid", "nic": "mac"},
                }
            return {
                "path": str(candidate),
                "format": "ini",
                "section": _guess_ini_section(candidate),
            }
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

    return "ui_automation", {
        "window_title_re": "系统登录|登录|管理信息系统",
        "window_class_re": "#32770|ThunderRT6FormDC",
        "wait_timeout_sec": 15,
    }


def _looks_like_login_config(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix == ".properties":
        return _looks_like_properties_login(path)

    if path.suffix.lower() == ".ini":
        parser = configparser.ConfigParser()
        try:
            parser.read(path, encoding="utf-8")
        except (configparser.Error, OSError):
            return False
        for section in parser.sections():
            keys = {key.lower() for key in parser.options(section)}
            if len(keys & LOGIN_KEYWORDS) >= 2:
                return True
        return False

    try:
        content = path.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return False
    pattern = r"(?i)(server|ip|userid|user_id|mac|nic|password|pwd)\s*[:=]"
    return re.search(pattern, content) is not None


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


def _looks_like_properties_login(path: Path) -> bool:
    try:
        content = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return False

    keys: set[str] = set()
    for line in content:
        raw = line.strip()
        if not raw or raw.startswith("#") or raw.startswith("!"):
            continue
        if "=" not in raw:
            continue
        key = raw.split("=", 1)[0].strip().lower()
        if key:
            keys.add(key)
    return len(keys & LOGIN_KEYWORDS) >= 2


def _first_existing(*paths: Path) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None
