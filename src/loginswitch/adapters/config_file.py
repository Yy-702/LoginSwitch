from __future__ import annotations

import configparser
from pathlib import Path

from loginswitch.models import Profile


class ConfigFileAdapter:
    def apply(self, profile: Profile, credential: dict[str, str | None]) -> None:
        raw_path = profile.adapter_config.get("path")
        if not raw_path:
            return

        path = Path(raw_path)
        file_format = profile.adapter_config.get("format", "ini")
        if file_format == "properties" or path.suffix.lower() == ".properties":
            self._apply_properties(path, profile)
            return

        self._apply_ini(path, profile, credential)

    def _apply_ini(
        self,
        path: Path,
        profile: Profile,
        credential: dict[str, str | None],
    ) -> None:
        parser = configparser.ConfigParser()
        if path.exists():
            parser.read(path, encoding="utf-8")

        section = profile.adapter_config.get("section", "Login")
        if not parser.has_section(section):
            parser.add_section(section)

        parser.set(section, "server", profile.env.server)
        parser.set(section, "user_id", profile.account.user_id)
        parser.set(section, "role", profile.account.role)
        parser.set(section, "nic", profile.account.nic)

        password = credential.get("password")
        if password:
            parser.set(section, "password", password)

        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            parser.write(f)

    def _apply_properties(self, path: Path, profile: Profile) -> None:
        key_map = profile.adapter_config.get(
            "keyMap",
            {"server": "ip", "userId": "userid", "nic": "mac"},
        )
        target_values = {
            key_map.get("server", "ip"): profile.env.server,
            key_map.get("userId", "userid"): profile.account.user_id,
            key_map.get("nic", "mac"): profile.account.nic,
        }

        lines: list[str] = []
        if path.exists():
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()

        seen: set[str] = set()
        new_lines: list[str] = []
        for line in lines:
            if "=" not in line:
                new_lines.append(line)
                continue
            key, _ = line.split("=", 1)
            normalized_key = key.strip()
            if normalized_key in target_values:
                new_lines.append(f"{normalized_key}={target_values[normalized_key]}")
                seen.add(normalized_key)
            else:
                new_lines.append(line)

        for key, value in target_values.items():
            if key not in seen:
                new_lines.append(f"{key}={value}")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
