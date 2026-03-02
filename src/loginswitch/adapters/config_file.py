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
