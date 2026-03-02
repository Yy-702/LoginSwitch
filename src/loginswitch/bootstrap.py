from __future__ import annotations

from pathlib import Path

from .adapters.config_file import ConfigFileAdapter
from .adapters.registry import RegistryAdapter
from .adapters.ui_automation import UIAutomationAdapter
from .audit import AuditLogger
from .confirm import ProductionConfirmer
from .credentials import CredentialStore
from .launcher import LauncherService
from .paths import app_data_dir
from .storage import ProfileStore


def build_services() -> tuple[ProfileStore, CredentialStore, LauncherService]:
    base_dir = app_data_dir()
    profile_store = ProfileStore(base_dir / "profiles.json")
    cred_store = CredentialStore("LoginSwitch")
    audit = AuditLogger(base_dir / "audit.log")
    adapters = {
        "config_file": ConfigFileAdapter(),
        "registry": RegistryAdapter(),
        "ui_automation": UIAutomationAdapter(),
    }
    launcher = LauncherService(
        credential_store=cred_store,
        adapters=adapters,
        process_launcher=_ProcessLauncherCompat(),
        audit_logger=audit,
        confirmer=ProductionConfirmer(),
    )
    return profile_store, cred_store, launcher


class _ProcessLauncherCompat:
    def launch(self, app_path: str) -> None:
        from .process_launcher import ProcessLauncher

        ProcessLauncher().launch(app_path)
