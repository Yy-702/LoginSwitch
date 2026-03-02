from __future__ import annotations

import keyring
from keyring.errors import KeyringError


class CredentialStore:
    def __init__(self, service_name: str = "LoginSwitch"):
        self.service_name = service_name

    def save_credential(self, profile_id: str, username: str, password: str) -> bool:
        try:
            keyring.set_password(self.service_name, f"{profile_id}:username", username)
            keyring.set_password(self.service_name, f"{profile_id}:password", password)
            return True
        except KeyringError:
            return False

    def load_credential(self, profile_id: str) -> dict[str, str | None]:
        username = keyring.get_password(self.service_name, f"{profile_id}:username")
        password = keyring.get_password(self.service_name, f"{profile_id}:password")
        return {"username": username, "password": password}

    def delete_credential(self, profile_id: str) -> bool:
        ok = True
        for suffix in ("username", "password"):
            try:
                keyring.delete_password(self.service_name, f"{profile_id}:{suffix}")
            except KeyringError:
                ok = False
        return ok
